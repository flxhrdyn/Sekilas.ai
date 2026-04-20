from __future__ import annotations

import uuid
from typing import Any
from typing import Mapping
from typing import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, Range
from datetime import datetime, timedelta, timezone

from backend.agents.models import FilteredArticle, RawArticle


ArticleLike = RawArticle | FilteredArticle


class QdrantVectorStore:
    def __init__(self, url: str, api_key: str, collection_name: str = "sekilas_ai") -> None:
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key)

    def delete_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
            print(f"[OK] Collection '{self.collection_name}' berhasil dihapus.")

    def ensure_collection(self, vector_size: int = 768) -> None:
        if self.client.collection_exists(self.collection_name):
            info = self.client.get_collection(self.collection_name)
            existing_size = self._extract_vector_size(info)
            if existing_size is not None and existing_size != vector_size:
                raise RuntimeError(
                    "Ukuran vector collection tidak cocok: "
                    f"collection={existing_size}, embedding_model={vector_size}. "
                    "Gunakan nama collection baru atau samakan model embedding."
                )
            # Pastikan index selalu ada (aman dipanggil berulang kali)
            from qdrant_client.models import PayloadSchemaType
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="published_at_ts",
                field_schema=PayloadSchemaType.FLOAT,
            )
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        # Tambahkan index untuk kolom filtering TTL
        from qdrant_client.models import PayloadSchemaType
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="published_at_ts",
            field_schema=PayloadSchemaType.FLOAT,
        )

    def upsert_articles(
        self,
        articles: Sequence[ArticleLike],
        embeddings: Sequence[Sequence[float]],
        insights_by_url: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        if len(articles) != len(embeddings):
            raise ValueError("Jumlah artikel dan embedding harus sama.")

        points: list[PointStruct] = []
        for article, vector in zip(articles, embeddings, strict=True):
            category = getattr(article, "category", article.category_hint)
            insight = insights_by_url.get(article.url, {}) if insights_by_url else {}
            summary = str(insight.get("summary", "")).strip()
            raw_points = insight.get("key_points", [])
            key_points = [str(item).strip() for item in raw_points if str(item).strip()]
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, article.url)),
                    vector=list(vector),
                    payload={
                        "url": article.url,
                        "title": article.title,
                        "source": article.source,
                        "category": category,
                        "published_at": article.published_at.isoformat(),
                        "published_at_ts": article.published_at.timestamp(),
                        "summary": summary,
                        "key_points": key_points,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def cleanup_old_articles(self, days: int) -> int:
        """Menghapus artikel yang lebih tua dari jumlah hari tertentu."""
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
        threshold_ts = threshold_date.timestamp()
        
        print(f"[PROCESS] Membersihkan artikel lebih tua dari {threshold_date.isoformat()} ({days} hari)...")
        
        # Hitung sebelum
        count_before = self.count()
        
        # Lakukan penghapusan berdasarkan payload 'published_at_ts' (numerik)
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="published_at_ts",
                        range=Range(lt=threshold_ts)
                    )
                ]
            )
        )
        
        # Hitung sesudah
        count_after = self.count()
        deleted_count = count_before - count_after
        
        if deleted_count > 0:
            print(f"[OK] Berhasil membersihkan {deleted_count} artikel lama dari Qdrant.")
        else:
            print(f"[INFO] Tidak ada artikel lama yang perlu dibersihkan.")
            
        return deleted_count

    def count(self) -> int:
        return self.client.count(collection_name=self.collection_name, exact=True).count

    @staticmethod
    def _extract_vector_size(collection_info: Any) -> int | None:
        vectors = getattr(collection_info.config.params, "vectors", None)
        if vectors is None:
            return None

        size = getattr(vectors, "size", None)
        if isinstance(size, int):
            return size

        if isinstance(vectors, dict):
            for value in vectors.values():
                candidate = getattr(value, "size", None)
                if isinstance(candidate, int):
                    return candidate

        return None
