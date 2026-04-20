import json
from pathlib import Path
from typing import Any, List, Optional
from backend.agents.embedder import NewsEmbedder, get_embedder
from backend.config.settings import get_settings
from backend.rag.qa_chain import NewsQAChain
from backend.rag.retriever import NewsRetriever


class NewsService:
    @staticmethod
    def load_summaries() -> list[dict[str, Any]]:
        settings = get_settings()
        if not settings.summaries_file.exists():
            return []
        try:
            raw = json.loads(settings.summaries_file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict) and ("item_count" in item or "top_stories" in item or "category_digests" in item)]

    @staticmethod
    def get_latest_digest() -> dict[str, Any] | None:
        digests = NewsService.load_summaries()
        return digests[-1] if digests else None

    @staticmethod
    def get_retriever() -> NewsRetriever:
        settings = get_settings()
        embedder = get_embedder(
            model_name=settings.embedding_model,
            output_dimensionality=settings.embedding_output_dim,
        )
        return NewsRetriever(
            embedder=embedder,
            qdrant_url=settings.qdrant_url,
            qdrant_api_key=settings.qdrant_api_key,
            collection_name=settings.qdrant_collection,
        )

    @staticmethod
    def get_qdrant_metrics() -> dict[str, Any]:
        """Calculates current total and percentage change vs previous day, handling resets."""
        digests = NewsService.load_summaries()
        if not digests:
            return {"total": 0, "percent_change": 0}
        
        latest = digests[-1]
        stats = latest.get("pipeline_stats", {})
        curr_total = stats.get("total_in_qdrant", latest.get("total_in_qdrant", 0))
        
        # Determine "Baseline"
        # We look for the most recent record from a different date
        curr_date = latest.get("date") or latest.get("timestamp", "")[:10]
        prev_day_total = 0
        
        for d in reversed(digests[:-1]):
            d_date = d.get("date") or d.get("timestamp", "")[:10]
            if d_date != curr_date:
                d_stats = d.get("pipeline_stats", {})
                prev_day_total = d_stats.get("total_in_qdrant", d.get("total_in_qdrant", 0))
                break
        
        # RESET DETECTION:
        # If curr_total is significantly lower than prev_day_total, a reset happened.
        # In this case, we find the local minimum encounterd today/recently and compare to that.
        if prev_day_total > curr_total:
            # Find the lowest total seen since the "drop"
            local_min = curr_total
            for d in reversed(digests[:-1]):
                d_total = d.get("pipeline_stats", {}).get("total_in_qdrant", d.get("total_in_qdrant", 0))
                if d_total < local_min:
                    local_min = d_total
                if d_total > curr_total * 2: # Found the pre-reset peak
                    break
            
            baseline = local_min
        else:
            baseline = prev_day_total if prev_day_total > 0 else (digests[-2].get("pipeline_stats", {}).get("total_in_qdrant", digests[-2].get("total_in_qdrant", 0)) if len(digests) > 1 else 0)

        percent_change = 0
        if baseline > 0 and curr_total >= baseline:
            percent_change = ((curr_total - baseline) / baseline) * 100
        elif baseline > 0 and curr_total < baseline:
            # If for some reason it's still lower, just show a small negative or 0
            percent_change = ((curr_total - baseline) / baseline) * 100
            
        return {
            "total": curr_total,
            "percent_change": round(percent_change, 1)
        }

    @staticmethod
    def get_qa_chain() -> NewsQAChain:
        settings = get_settings()
        retriever = NewsService.get_retriever()
        return NewsQAChain(
            retriever=retriever,
            api_key=settings.gemini_api_key,
            model=settings.qa_model,
            default_top_k=settings.qa_top_k,
        )
