from __future__ import annotations

import sys
import random
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TypedDict

from backend.agents.embedder import NewsEmbedder, get_embedder
from backend.agents.filter import NewsFilterAgent
from backend.agents.notifier import TelegramNotifier
from backend.agents.summarizer import NewsSummarizerAgent, build_daily_digest_record
from backend.agents.models import prepare_document
from backend.agents.scraper import NewsScraper
from backend.config.settings import ROOT_DIR, get_settings
from langgraph.graph import END, StateGraph
from backend.rag.vector_store import QdrantVectorStore


class NewsState(TypedDict, total=False):
    raw_articles: list
    all_processed: set[str]
    filtered_articles: list
    filter_stats: dict
    insights: dict
    headline: str
    embeddings: list[list[float]]
    total_in_qdrant: int
    notifier_status: str
    result: dict


def _append_json_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    else:
        existing = []

    existing.append(record)
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_graph(
    scraper: NewsScraper,
    embedder: NewsEmbedder,
    filter_agent: NewsFilterAgent,
    summarizer: NewsSummarizerAgent,
    store: QdrantVectorStore,
    notifier: TelegramNotifier | None,
    max_per_source: int = 40,
) -> StateGraph:
    def scrape_node(_: NewsState) -> NewsState:
        print("[PROCESS] Memulai proses scraping dari sumber...")
        articles, all_processed = scraper.scrape_new_articles(max_per_source=max_per_source)
        
        # Acak urutan artikel untuk menjamin diversitas sumber berita (Nasional & Internasional)
        random.shuffle(articles)
        
        # Batasi pengambilan awal agar tidak terlalu membengkak (Maks 50 berita mentah)
        articles = articles[:50]
        
        print(f"[OK] Scraping selesai. Mengambil {len(articles)} berita untuk diolah.")
        return {"raw_articles": articles, "all_processed": all_processed}

    def route_after_scrape(state: NewsState) -> str:
        return "no-new-articles" if not state.get("raw_articles") else "filter"

    def no_new_articles_node(state: NewsState) -> NewsState:
        scraper.save_processed_urls(state.get("all_processed", set()))
        return {
            "result": {
                "status": "no-new-articles",
                "raw_articles": 0,
                "filtered_articles": 0,
                "summarized_articles": 0,
                "ingested": 0,
                "total_in_qdrant": None,
            }
        }

    def filter_node(state: NewsState) -> NewsState:
        print(f"[PROCESS] Memfilter dan menduplikasi {len(state['raw_articles'])} artikel...")
        raw_articles = state.get("raw_articles", [])
        filtered_articles, filter_stats = filter_agent.run(raw_articles)
        
        # Batasi maksimal 25 berita terbaik yang lolos filter untuk diringkas (Optimasi Kecepatan)
        filtered_articles = filtered_articles[:25]
        
        print(f"[OK] Filter selesai. {len(filtered_articles)} artikel tersisa untuk diringkas.")
        return {
            "filtered_articles": filtered_articles,
            "filter_stats": {
                "total_input": filter_stats.total_input,
                "too_short_discarded": filter_stats.too_short_discarded,
                "duplicate_discarded": filter_stats.duplicate_discarded,
                "passed": filter_stats.passed,
            },
        }

    def route_after_filter(state: NewsState) -> str:
        return "all-filtered-out" if not state.get("filtered_articles") else "summarize"

    def all_filtered_node(state: NewsState) -> NewsState:
        print("[INFO] Semua artikel difilter keluar.")
        scraper.save_processed_urls(state.get("all_processed", set()))
        stats = state.get("filter_stats", {})
        return {
            "result": {
                "status": "all-filtered-out",
                "raw_articles": len(state.get("raw_articles", [])),
                "filtered_articles": 0,
                "summarized_articles": 0,
                "too_short_discarded": stats.get("too_short_discarded", 0),
                "duplicate_discarded": stats.get("duplicate_discarded", 0),
                "ingested": 0,
                "total_in_qdrant": None,
            }
        }

    def summarize_node(state: NewsState) -> NewsState:
        print(f"[PROCESS] Membuat ringkasan untuk {len(state['filtered_articles'])} artikel...")
        filtered_articles = state.get("filtered_articles", [])
        insights = summarizer.build_insights(filtered_articles)
        headline = summarizer.generate_daily_headline(filtered_articles, insights)
        insights_payload = {
            url: {"summary": insight.summary, "key_points": insight.key_points}
            for url, insight in insights.items()
        }
        print("[OK] Ringkasan dan headline berhasil dibuat.")
        return {
            "insights": insights,
            "headline": headline,
        }

    def embed_node(state: NewsState) -> NewsState:
        print(f"[PROCESS] Membuat embedding untuk {len(state['filtered_articles'])} artikel...")
        filtered_articles = state.get("filtered_articles", [])
        docs = [prepare_document(article) for article in filtered_articles]
        embeddings = embedder.embed_documents(docs)
        print("[OK] Embedding selesai.")
        return {"embeddings": embeddings}

    def upsert_and_persist_node(state: NewsState) -> NewsState:
        print("[PROCESS] Menyimpan data ke database dan mengirim notifikasi...")
        settings = get_settings()
        filtered_articles = state.get("filtered_articles", [])
        embeddings = state.get("embeddings", [])
        insights = state.get("insights", {})
        insights_payload = state.get("insights_payload", {})

        vector_size = len(embeddings[0]) if embeddings else (settings.embedding_output_dim or 768)
        store.ensure_collection(vector_size=vector_size)
        
        # Format payload untuk upsert
        insights_payload = {
            url: {"summary": insight.summary, "key_points": insight.key_points}
            for url, insight in insights.items()
        }
        store.upsert_articles(filtered_articles, embeddings, insights_by_url=insights_payload)

        scraper.save_processed_urls(state.get("all_processed", set()))

        total = store.count()
        digest_record = build_daily_digest_record(
            filtered_articles,
            insights,
            state.get("headline", ""),
        )
        filter_stats = state.get("filter_stats", {})
        digest_record.update(
            {
                "pipeline_stats": {
                    "raw_articles": len(state.get("raw_articles", [])),
                    "filtered_articles": len(filtered_articles),
                    "too_short_discarded": filter_stats.get("too_short_discarded", 0),
                    "duplicate_discarded": filter_stats.get("duplicate_discarded", 0),
                    "ingested": len(filtered_articles),
                    "total_in_qdrant": total,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        _append_json_record(settings.summaries_file, digest_record)

        notifier_status = "disabled"
        if notifier is not None:
            try:
                notifier.send_digest(digest_record)
                notifier_status = "sent"
            except Exception as exc:
                notifier_status = f"failed: {exc}"

        return {
            "total_in_qdrant": total,
            "notifier_status": notifier_status,
            "result": {
                "status": "ok",
                "raw_articles": len(state.get("raw_articles", [])),
                "filtered_articles": len(filtered_articles),
                "summarized_articles": len(insights),
                "headline": state.get("headline", ""),
                "too_short_discarded": filter_stats.get("too_short_discarded", 0),
                "duplicate_discarded": filter_stats.get("duplicate_discarded", 0),
                "ingested": len(filtered_articles),
                "total_in_qdrant": total,
                "notifier_status": notifier_status,
            },
        }

    builder = StateGraph(NewsState)
    builder.add_node("scrape", scrape_node)
    builder.add_node("no-new-articles", no_new_articles_node)
    builder.add_node("filter", filter_node)
    builder.add_node("all-filtered-out", all_filtered_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("embed", embed_node)
    builder.add_node("upsert-and-persist", upsert_and_persist_node)

    builder.set_entry_point("scrape")
    builder.add_conditional_edges(
        "scrape",
        route_after_scrape,
        {"no-new-articles": "no-new-articles", "filter": "filter"},
    )
    builder.add_conditional_edges(
        "filter",
        route_after_filter,
        {"all-filtered-out": "all-filtered-out", "summarize": "summarize"},
    )
    builder.add_edge("summarize", "embed")
    builder.add_edge("embed", "upsert-and-persist")
    builder.add_edge("no-new-articles", END)
    builder.add_edge("all-filtered-out", END)
    builder.add_edge("upsert-and-persist", END)
    return builder


def run_pipeline() -> dict:
    settings = get_settings()

    scraper = NewsScraper(
        sources_file=settings.sources_file,
        processed_urls_file=settings.processed_urls_file,
        timeout_seconds=settings.request_timeout_seconds,
        user_agent=settings.user_agent,
    )

    embedder = get_embedder(
        model_name=settings.embedding_model,
        output_dimensionality=settings.embedding_output_dim,
    )

    filter_agent = NewsFilterAgent(
        embedder=embedder,
        api_key=settings.gemini_api_key,
        classifier_model=settings.classifier_model,
        dedup_threshold=settings.dedup_threshold,
        min_content_chars=settings.min_content_chars,
    )

    summarizer = NewsSummarizerAgent(
        api_key=settings.gemini_api_key,
        model=settings.summarizer_model,
        max_content_chars=settings.summary_max_content_chars,
    )

    store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )

    notifier: TelegramNotifier | None = None
    if settings.enable_telegram_notify and settings.telegram_bot_token and settings.telegram_chat_id:
        notifier = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            dashboard_url=settings.dashboard_url,
            timeout_seconds=settings.request_timeout_seconds,
        )

    graph = _build_graph(
        scraper, embedder, filter_agent, summarizer, store, notifier, max_per_source=settings.max_per_source
    ).compile()
    final_state = graph.invoke({"result": {}})
    return final_state.get("result", {"status": "unknown"})


def main() -> None:
    result = run_pipeline()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
