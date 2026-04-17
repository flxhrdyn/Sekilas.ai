from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from backend.agents.embedder import NewsEmbedder


@dataclass(slots=True)
class SearchResult:
    url: str
    title: str
    source: str
    category: str
    published_at: str
    summary: str
    key_points: list[str]
    score: float
    payload: dict[str, Any]


class NewsRetriever:
    def __init__(
        self,
        embedder: NewsEmbedder,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str,
    ) -> None:
        self.embedder = embedder
        self.collection_name = collection_name
        self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
    ) -> list[SearchResult]:
        query_vector = self.embedder.embed_query(query)

        query_filter: Filter | None = None
        if category_filter and category_filter.lower() != "semua":
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category_filter),
                    )
                ]
            )

        points = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        results: list[SearchResult] = []
        for point in points:
            payload = dict(point.payload or {})
            raw_key_points = payload.get("key_points", [])
            key_points = [str(item) for item in raw_key_points if str(item).strip()]
            results.append(
                SearchResult(
                    url=str(payload.get("url", "")),
                    title=str(payload.get("title", "Tanpa judul")),
                    source=str(payload.get("source", "Unknown")),
                    category=str(payload.get("category", "Umum")),
                    published_at=str(payload.get("published_at", "")),
                    summary=str(payload.get("summary", "")),
                    key_points=key_points,
                    score=float(point.score),
                    payload=payload,
                )
            )

        return results


def build_context(results: list[SearchResult], max_chars: int = 5000) -> str:
    if not results:
        return ""

    chunks: list[str] = []
    for idx, item in enumerate(results, start=1):
        summary = item.summary.strip()
        key_points = " | ".join(item.key_points[:3])
        chunks.append(
            "\n".join(
                [
                    f"[{idx}] Judul: {item.title}",
                    f"Kategori: {item.category}",
                    f"Sumber: {item.source}",
                    f"URL: {item.url}",
                    f"Ringkasan: {summary}",
                    f"Poin penting: {key_points}",
                ]
            )
        )

    context = "\n\n".join(chunks)
    return context[:max_chars]
