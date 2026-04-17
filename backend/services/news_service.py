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
        return [item for item in raw if isinstance(item, dict) and "category_digests" in item]

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
    def get_qa_chain() -> NewsQAChain:
        settings = get_settings()
        retriever = NewsService.get_retriever()
        return NewsQAChain(
            retriever=retriever,
            api_key=settings.gemini_api_key,
            model=settings.qa_model,
            default_top_k=settings.qa_top_k,
        )
