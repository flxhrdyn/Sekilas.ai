from backend.config.settings import get_settings
from backend.rag.vector_store import QdrantVectorStore


def main() -> None:
    settings = get_settings()
    
    store = QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )
    
    print(f"[PROCESS] Menghapus data dari collection '{settings.qdrant_collection}'...")
    store.delete_collection()
    print("[OK] Vector DB kosong. Silakan jalankan 'python -m backend.scripts.init_vector_db' untuk membuat ulang.")


if __name__ == "__main__":
    main()
