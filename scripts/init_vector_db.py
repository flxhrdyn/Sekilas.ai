from agents.embedder import GeminiEmbedder
from config.settings import get_settings
from rag.vector_store import QdrantVectorStore


def main() -> None:
    settings = get_settings()
    embedder = GeminiEmbedder(
        api_key=settings.gemini_api_key,
        model=settings.embedding_model,
        output_dimensionality=settings.embedding_output_dim,
    )
    vector_size = len(embedder.embed_query("dimension probe"))

    store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )
    store.ensure_collection(vector_size=vector_size)
    print(
        f"Collection '{settings.qdrant_collection}' siap. "
        f"Model: {embedder.model}, dimensi: {vector_size}."
    )


if __name__ == "__main__":
    main()
