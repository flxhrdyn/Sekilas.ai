from __future__ import annotations

import uuid
from typing import Any
from typing import Mapping
from typing import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, Range, SparseVectorParams, SparseIndexParams, Modifier
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

    def ensure_collection(self, vector_size: int = 384) -> None:
        if self.client.collection_exists(self.collection_name):
            info = self.client.get_collection(self.collection_name)
            existing_size = self._extract_vector_size(info)
            if existing_size is not None and existing_size != vector_size:
                raise RuntimeError(
                    "Ukuran vector collection tidak cocok: "
                    f"collection={existing_size}, embedding_model={vector_size}. "
                    "Gunakan nama collection baru atau samakan model embedding."
                )
            return
            
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=vector_size, distance=Distance.COSINE)},
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False),
                    modifier=Modifier.IDF
                )
            }
        )
        # Tambahkan index untuk kolom filtering TTL
        from qdrant_client.models import PayloadSchemaType
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="published_at_ts",
            field_schema=PayloadSchemaType.FLOAT,
        )

    def upsert_chunks(
        self,
        chunks: Sequence[dict], # List of dicts containing chunk data and embeddings
    ) -> None:
        if not chunks:
            return

        points: list[PointStruct] = []
        for chunk in chunks:
            # We create a unique ID for each chunk using URL + Chunk Index
            chunk_id_str = f"{chunk['url']}#chunk_{chunk['chunk_index']}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id_str))
            
            vector_dict = {
                "dense": list(chunk["dense_embedding"]),
                "sparse": chunk["sparse_embedding"]
            }
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector_dict,
                    payload={
                        "url": chunk["url"],
                        "title": chunk["title"],
                        "source": chunk["source"],
                        "category": chunk["category"],
                        "published_at": chunk["published_at"],
                        "published_at_ts": chunk["published_at_ts"],
                        "text_chunk": chunk["text_chunk"],
                        "chunk_index": chunk["chunk_index"],
                        "summary": chunk.get("summary", ""),
                        "key_points": chunk.get("key_points", []),
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
        
        count_before = self.count()
        
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
        
        count_after = self.count()
        deleted_count = count_before - count_after
        
        if deleted_count > 0:
            print(f"[OK] Berhasil membersihkan {deleted_count} chunk lama dari Qdrant.")
        else:
            print(f"[INFO] Tidak ada chunk lama yang perlu dibersihkan.")
            
        return deleted_count

    def count(self) -> int:
        return self.client.count(collection_name=self.collection_name, exact=True).count

    @staticmethod
    def _extract_vector_size(collection_info: Any) -> int | None:
        vectors = getattr(collection_info.config.params, "vectors", None)
        if vectors is None:
            return None

        # Check for named vectors ("dense")
        if isinstance(vectors, dict):
            dense_cfg = vectors.get("dense")
            if dense_cfg:
                size = getattr(dense_cfg, "size", None)
                if isinstance(size, int):
                    return size
            
            for value in vectors.values():
                candidate = getattr(value, "size", None)
                if isinstance(candidate, int):
                    return candidate

        return None
