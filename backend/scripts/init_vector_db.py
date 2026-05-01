from backend.agents.embedder import NewsEmbedder, get_embedder
from backend.config.settings import get_settings
from backend.rag.vector_store import QdrantVectorStore


def main() -> None:
    settings = get_settings()
    embedder = get_embedder(
        model_name=settings.embedding_model,
        output_dimensionality=settings.embedding_output_dim,
    )
    dense_vec, _ = embedder.embed_query("dimension probe")
    vector_size = len(dense_vec)

    store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )
    store.ensure_collection(vector_size=vector_size)
    print(
        f"Collection '{settings.qdrant_collection}' siap. "
        f"Model: {settings.embedding_model}, dimensi: {vector_size}."
    )


if __name__ == "__main__":
    main()
