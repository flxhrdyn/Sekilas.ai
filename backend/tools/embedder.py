from __future__ import annotations

import time
from typing import Sequence
import logging

try:
    from fastembed import TextEmbedding, SparseTextEmbedding
except ImportError:
    pass # Will be handled by requirements

logger = logging.getLogger(__name__)

class NewsEmbedder:
    """
    Menghasilkan dense dan sparse embeddings menggunakan FastEmbed (CPU-Optimized, ONNX).
    """
    def __init__(
        self,
        dense_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        sparse_model_name: str = "Qdrant/bm25"
    ) -> None:
        print(f"[INIT] Memuat FastEmbed Dense model: {dense_model_name}...")
        start_time = time.time()
        self.dense_model = TextEmbedding(model_name=dense_model_name)
        print(f"[OK] Dense Model dimuat dalam {time.time() - start_time:.2f} detik.")
        
        print(f"[INIT] Memuat FastEmbed Sparse model: {sparse_model_name}...")
        start_time = time.time()
        self.sparse_model = SparseTextEmbedding(model_name=sparse_model_name)
        print(f"[OK] Sparse Model dimuat dalam {time.time() - start_time:.2f} detik.")

    def embed_documents(self, texts: Sequence[str]) -> tuple[list[list[float]], list[dict]]:
        """
        Menghasilkan Dense dan Sparse embeddings secara bersamaan.
        """
        if not texts:
            return [], []
            
        print(f"[PROCESS] Generating Dense Embeddings untuk {len(texts)} dokumen...")
        dense_embeddings_gen = self.dense_model.embed(texts)
        dense_embeddings = [list(vec) for vec in dense_embeddings_gen]
        
        print(f"[PROCESS] Generating Sparse Embeddings (BM25) untuk {len(texts)} dokumen...")
        sparse_embeddings_gen = self.sparse_model.embed(texts) # Sparse doesn't need prefix
        sparse_embeddings = [
            {"indices": list(vec.indices), "values": list(vec.values)} 
            for vec in sparse_embeddings_gen
        ]
        
        return dense_embeddings, sparse_embeddings

    def embed_query(self, query: str) -> tuple[list[float], dict]:
        """
        Menghasilkan Dense dan Sparse embeddings untuk kueri pencarian.
        """
        dense_gen = self.dense_model.embed([query])
        dense_vec = list(list(dense_gen)[0])
        
        sparse_gen = self.sparse_model.embed([query])
        sparse_res = list(sparse_gen)[0]
        sparse_vec = {"indices": list(sparse_res.indices), "values": list(sparse_res.values)}
        
        return dense_vec, sparse_vec

_embedder_instance: NewsEmbedder | None = None

def get_embedder(
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    output_dimensionality: int | None = None,
) -> NewsEmbedder:
    """
    Singleton provider for NewsEmbedder.
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = NewsEmbedder(dense_model_name=model_name)
    else:
        # Opsional: Log jika model sudah ada di memori
        pass
    return _embedder_instance
