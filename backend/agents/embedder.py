from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class NewsEmbedder:
    """
    Local Embedding Agent using Sentence-Transformers (e.g., all-MiniLM-L6-v2).
    This agent runs locally to avoid API rate limits and costs.
    """

    def __init__(
        self,
        api_key: str | None = None,  # Kept for compatibility, not used for local
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        output_dimensionality: int | None = 384,
    ) -> None:
        self.model_name = model
        self.output_dimensionality = output_dimensionality
        self._client = None
        
    @property
    def client(self):
        """Lazy loader for the SentenceTransformer model."""
        if self._client is None:
            print(f"[INFO] Memuat Model Embedding Lokal (Lazy): {self.model_name}...")
            try:
                self._client = SentenceTransformer(self.model_name)
                print(f"[OK] Model {self.model_name} siap digunakan.")
            except Exception as e:
                logger.error(f"Gagal memuat model embedding {self.model_name}: {e}")
                raise
        return self._client

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """Embed a single piece of text."""
        embedding = self.client.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(
        self, docs: Sequence[str], batch_size: int = 32, task_type: str = "retrieval_document"
    ) -> list[list[float]]:
        """
        Embed a list of documents in one go.
        Local models handle large batches much more efficiently than APIs.
        """
        if not docs:
            return []
            
        print(f"[PROCESS] Local Embedding: Memproses {len(docs)} dokumen...")
        
        # Bersihkan docs dari string kosong
        valid_docs = [doc if doc and doc.strip() else "empty" for doc in docs]
        
        embeddings = self.client.encode(
            valid_docs, 
            batch_size=batch_size, 
            show_progress_bar=False,
            normalize_embeddings=True
        )
        
        print(f"[OK] Selesai melakukan embedding untuk {len(docs)} dokumen.")
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query."""
        return self.embed_text(query, task_type="retrieval_query")

# Forward compatibility ended, using NewsEmbedder everywhere now.

_embedder_instance: NewsEmbedder | None = None

def get_embedder(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
    output_dimensionality: int = 384
) -> NewsEmbedder:
    """
    Singleton provider for NewsEmbedder to avoid loading 
    large models multiple times in memory.
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = NewsEmbedder(model=model_name, output_dimensionality=output_dimensionality)
    return _embedder_instance
