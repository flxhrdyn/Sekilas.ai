import sys
import os
from pathlib import Path

# Add root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from backend.config.settings import get_settings
from backend.services.news_service import NewsService

def test_search():
    print("--- TESTING HYBRID + RERANK SEARCH ---")
    query = "kecelakaan kereta api"
    print(f"Query: {query}\n")
    
    retriever = NewsService.get_retriever()
    reranker = NewsService.get_reranker()
    
    # Test 1: Tanpa Rerank (Hanya RRF)
    print("1. Hasil TANPA Rerank (Original RRF):")
    results_raw = retriever.search(query, top_k=5, reranker=None)
    for i, r in enumerate(results_raw):
        print(f"[{i+1}] {r.title} (Score: {r.score:.4f})")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Dengan Rerank (Llama 3.1 8B)
    print("2. Hasil DENGAN Rerank (Llama 3.1 8B):")
    results_reranked = retriever.search(query, top_k=5, reranker=reranker)
    for i, r in enumerate(results_reranked):
        print(f"[{i+1}] {r.title} (Score: {r.score:.4f})")
    print("----------------------")

if __name__ == "__main__":
    test_search()
