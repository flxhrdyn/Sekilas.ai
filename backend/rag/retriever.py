from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, Prefetch, SparseVector, FusionQuery, Fusion

from backend.agents.embedder import NewsEmbedder


@dataclass(slots=True)
class SearchResult:
    url: str
    title: str
    source: str
    category: str
    published_at: str
    text_chunk: str
    chunk_index: int
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
        dense_vec, sparse_vec = self.embedder.embed_query(query)

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

        # Hybrid Search using Prefetch and Reciprocal Rank Fusion (RRF)
        prefetch_dense = Prefetch(
            query=dense_vec,
            using="dense",
            filter=query_filter,
            limit=top_k * 2, # Fetch more for fusion
        )
        
        prefetch_sparse = Prefetch(
            query=SparseVector(indices=sparse_vec["indices"], values=sparse_vec["values"]),
            using="sparse",
            filter=query_filter,
            limit=top_k * 2,
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[prefetch_dense, prefetch_sparse],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
        )
        
        points = response.points

        results: list[SearchResult] = []
        for point in points:
            payload = dict(point.payload or {})
            results.append(
                SearchResult(
                    url=str(payload.get("url", "")),
                    title=str(payload.get("title", "Tanpa judul")),
                    source=str(payload.get("source", "Unknown")),
                    category=str(payload.get("category", "Umum")),
                    published_at=str(payload.get("published_at", "")),
                    text_chunk=str(payload.get("text_chunk", "")),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    score=float(point.score),
                    payload=payload,
                )
            )

        return results


def build_context(results: list[SearchResult], max_chars: int = 8000) -> str:
    if not results:
        return ""

    chunks: list[str] = []
    for idx, item in enumerate(results, start=1):
        chunks.append(
            "\n".join(
                [
                    f"[{idx}] Judul: {item.title}",
                    f"Kategori: {item.category}",
                    f"Sumber: {item.source}",
                    f"URL: {item.url}",
                    f"Kutipan Berita: {item.text_chunk}",
                ]
            )
        )

    context = "\n\n".join(chunks)
    return context[:max_chars]
