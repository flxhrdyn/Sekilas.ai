import sys
import os
from pathlib import Path

# Add root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from backend.config.settings import get_settings
from backend.services.news_service import NewsService

def test_search():
    print("--- TESTING SEARCH ---")
    query = "kecelakaan"
    print(f"Query: {query}")
    
    retriever = NewsService.get_retriever()
    results = retriever.search(query, top_k=5)
    
    print(f"Found {len(results)} results:")
    for i, r in enumerate(results):
        print(f"[{i+1}] {r.title} (Score: {r.score:.4f})")
        print(f"    Source: {r.source} | Category: {r.category}")
        print(f"    URL: {r.url}")
    print("----------------------")

if __name__ == "__main__":
    test_search()
