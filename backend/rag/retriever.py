from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, Prefetch, SparseVector, FusionQuery, Fusion

from backend.tools.embedder import NewsEmbedder


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
        reranker: Any | None = None,
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

        # Jika ada reranker, kita ambil lebih banyak kandidat (misal 15) untuk diurutkan ulang
        fetch_limit = max(top_k, 15) if reranker else top_k

        # Hybrid Search using Prefetch and Reciprocal Rank Fusion (RRF)
        prefetch_dense = Prefetch(
            query=dense_vec,
            using="dense",
            filter=query_filter,
            limit=fetch_limit * 2,
        )
        
        prefetch_sparse = Prefetch(
            query=SparseVector(indices=sparse_vec["indices"], values=sparse_vec["values"]),
            using="sparse",
            filter=query_filter,
            limit=fetch_limit * 2,
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[prefetch_dense, prefetch_sparse],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=fetch_limit,
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

        # Jalankan Reranking jika tersedia
        if reranker and results:
            results = reranker.rerank(query, results)
        
        # Deduplikasi berdasarkan URL agar satu berita tidak muncul berkali-kali
        unique_results: list[SearchResult] = []
        seen_urls = set()
        
        for res in results:
            if res.url not in seen_urls:
                unique_results.append(res)
                seen_urls.add(res.url)
        
        return unique_results[:top_k]


def build_context(results: list[SearchResult], max_chars: int = 8000) -> str:
    if not results:
        return ""

    context_parts: list[str] = []
    for idx, item in enumerate(results, start=1):
        # Format tanggal agar AI sadar waktu (Temporal Awareness)
        formatted_date = item.published_at
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%d %B %Y, %H:%M WIB")
        except:
            pass

        context_parts.append(
            f"--- DOKUMEN {idx} ---\n"
            f"JUDUL: {item.title}\n"
            f"SUMBER: {item.source} ({formatted_date})\n"
            f"WAKTU PUBLIKASI: {formatted_date}\n"
            f"RINGKASAN ARTIKEL: {item.payload.get('summary', '')}\n"
            f"ISI POTONGAN TEKS: {item.text_chunk}\n"
            f"URL: {item.url}"
        )
    
    context = "\n\n".join(context_parts)
    if len(context) > max_chars:
        context = context[:max_chars] + "\n... (konteks dipotong)"
    return context
