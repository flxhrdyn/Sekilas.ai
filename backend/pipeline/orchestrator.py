from __future__ import annotations

import sys
import random
import time
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TypedDict

from backend.agents.embedder import NewsEmbedder, get_embedder
from backend.agents.filter import NewsFilterAgent
from backend.agents.summarizer import NewsSummarizerAgent, build_daily_digest_record
from backend.agents.notifier import TelegramNotifier
from backend.agents.models import prepare_document, RawHeadline, FilteredArticle
from backend.agents.scraper import NewsScraper
from backend.agents.cluster_agent import NewsClusterAgent
from backend.config.settings import ROOT_DIR, get_settings
from langgraph.graph import END, StateGraph
from backend.rag.vector_store import QdrantVectorStore


class NewsState(TypedDict, total=False):
    raw_headlines: list[RawHeadline]
    all_processed: set[str]
    selected_headlines: list[RawHeadline]
    raw_articles: list
    filtered_articles: list
    filter_stats: dict
    insights: dict
    headline: str
    trending_topics_map: dict[int, str]
    story_syntheses: dict[int, dict]
    correlations: list[dict]
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


def _select_diverse_articles(articles: list[FilteredArticle], limit: int) -> list[FilteredArticle]:
    """
    Selects a balanced set of articles across categories, prioritizing 
    freshness (breaking news) and content depth.
    """
    if not articles:
        return []

    # 1. Group by category
    by_category: dict[str, list[FilteredArticle]] = {}
    for a in articles:
        by_category.setdefault(a.category, []).append(a)

    # 2. Sort each category by published_at (primary) and content length (secondary)
    for cat in by_category:
        by_category[cat].sort(
            key=lambda x: (x.published_at, len(x.content)),
            reverse=True
        )

    # 3. Round-robin selection to ensure diversity
    selected: list[FilteredArticle] = []
    categories = sorted(by_category.keys())  # Stable order for selection

    while len(selected) < limit and categories:
        to_remove = []
        for cat in categories:
            if by_category[cat]:
                selected.append(by_category[cat].pop(0))
                if len(selected) >= limit:
                    break
            else:
                to_remove.append(cat)

        for cat in to_remove:
            categories.remove(cat)

    # Sort final selection by date again for the digest
    selected.sort(key=lambda x: x.published_at, reverse=True)
    return selected


def _build_graph(
    scraper: NewsScraper,
    embedder: NewsEmbedder,
    filter_agent: NewsFilterAgent,
    cluster_agent: NewsClusterAgent,
    summarizer: NewsSummarizerAgent,
    store: QdrantVectorStore,
    notifier: TelegramNotifier | None,
    max_scan: int = 150,
) -> StateGraph:
    def scrape_node(_: NewsState) -> NewsState:
        print(f"[PROCESS] Memindai {max_scan} judul berita terbaru...")
        # Ambil total 120 judul (jatah fair-share per sumber diatur di dalam scraper)
        headlines, all_processed = scraper.fetch_new_headlines(max_total=120)
        
        # Shuffle agar urutan benar-benar variatif
        random.shuffle(headlines)
        headlines = headlines[:max_scan]
        
        print(f"[OK] Scanning selesai. Ditemukan {len(headlines)} judul baru dari berbagai sumber.")
        return {"raw_headlines": headlines, "all_processed": all_processed}

    def route_after_scrape(state: NewsState) -> str:
        return "no-new-articles" if not state.get("raw_headlines") else "cluster"

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

    def cluster_node(state: NewsState) -> NewsState:
        headlines = state.get("raw_headlines", [])
        clusters = cluster_agent.cluster_headlines(headlines)
        
        # Only name and track clusters with 2+ articles as 'Top Trending'
        # UNLESS user allows solo stories for top representatives
        potential_trending = [c for c in clusters if len(c) > 0][:5]
        
        # Identifikasi Nama Topik Tren (Map CID to Name)
        topic_names = summarizer.generate_trending_topics(potential_trending, top_k=5)
        
        trending_topics_map = {}
        for i, cluster in enumerate(potential_trending):
            if i < len(topic_names):
                trending_topics_map[cluster[0].cluster_id] = topic_names[i]
        
        # Seleksi beragam dari klaster
        # SELEKSI KETAT: Hanya ambil 18 artikel terbaik (satu per klaster)
        # Ini adalah bottleneck utama untuk menghemat API Gemini
        selected_headlines = cluster_agent.select_best_representatives(clusters, limit=18)
        
        return {
            "trending_topics_map": trending_topics_map,
            "selected_headlines": selected_headlines
        }

    def filter_node(state: NewsState) -> NewsState:
        selected_headlines = state.get("selected_headlines", [])
        
        # Download konten lengkap hanya untuk yang terpilih
        raw_articles = scraper.fetch_full_contents(selected_headlines)
        
        print(f"[PROCESS] Memfilter kualitas dan mengklasifikasi {len(raw_articles)} artikel...")
        filtered_articles, filter_stats = filter_agent.run(raw_articles)
        
        # Pastikan tetap dalam limit
        # Final selection untuk diringkas (maksimal 15 agar hemat API)
        filtered_articles = filtered_articles[:15]
        
        return {
            "raw_articles": raw_articles,
            "filtered_articles": filtered_articles,
            "filter_stats": {
                "total_input": filter_stats.total_input,
                "too_short_discarded": filter_stats.too_short_discarded,
                "duplicate_discarded": filter_stats.duplicate_discarded,
                "passed": len(filtered_articles),
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
        
        # Perform Story Synthesis for top clusters
        trending_map = state.get("trending_topics_map", {})
        story_syntheses = {}
        
        # Group filtered articles by cluster
        clusters_in_filtered = {}
        for a in filtered_articles:
            cid = getattr(a, "cluster_id", -1)
            if cid in trending_map:
                clusters_in_filtered.setdefault(cid, []).append(a)
        
        # Synthesize top groups
        for cid, group_articles in clusters_in_filtered.items():
            print(f"[PROCESS] Menyusun sintesis intelijen untuk topik: {trending_map[cid]}...")
            story_syntheses[cid] = summarizer.synthesize_story(group_articles, insights)
            time.sleep(2.0)

        # 7. Generate Headline Utama
        print("[PROCESS] Membuat headline utama hari ini...")
        headline = summarizer.generate_daily_headline(
            filtered_articles, 
            insights, 
            story_syntheses=story_syntheses, 
            trending_map=trending_map
        )

        # 8. Generate Strategic Correlations (Connect the dots)
        print("[PROCESS] Menganalisis kaitan strategis antar topik...")
        stories_for_correlation = []
        for cid, syn_data in story_syntheses.items():
            stories_for_correlation.append({
                "title": trending_map.get(cid, "Topik"),
                "synthesis": syn_data.get("synthesis", []),
                "impact_level": syn_data.get("impact_level", "LOW")
            })
        
        correlations = summarizer.generate_correlations(stories_for_correlation)
            
        print("[OK] Ringkasan, headline, dan korelasi strategis berhasil dibuat.")
        return {
            "insights": insights,
            "headline": headline,
            "story_syntheses": story_syntheses,
            "correlations": correlations,
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
            story_syntheses=state.get("story_syntheses", {}),
            trending_topics=state.get("trending_topics_map", {}),
            correlations=state.get("correlations", []),
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
    builder.add_node("cluster", cluster_node)
    builder.add_node("filter", filter_node)
    builder.add_node("all-filtered-out", all_filtered_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("embed", embed_node)
    builder.add_node("upsert-and-persist", upsert_and_persist_node)

    builder.set_entry_point("scrape")
    builder.add_conditional_edges(
        "scrape",
        route_after_scrape,
        {"no-new-articles": "no-new-articles", "cluster": "cluster"},
    )
    builder.add_edge("cluster", "filter")
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

    cluster_agent = NewsClusterAgent(
        embedder=embedder,
        similarity_threshold=0.72
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

    # Muat stats untuk logging awal
    from backend.config.monitor import SystemMonitor
    stats = SystemMonitor.get_stats()
    print(f"[INFO] Status Penggunaan Gemini Hari Ini: {stats.get('gemini_usage', 0)}/500")
    
    graph = _build_graph(
        scraper, embedder, filter_agent, cluster_agent, summarizer, store, notifier, max_scan=150
    ).compile()
    final_state = graph.invoke({"result": {}})
    return final_state.get("result", {"status": "unknown"})


def main() -> None:
    result = run_pipeline()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
