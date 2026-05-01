import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from backend.config.settings import get_settings
from backend.tools.filter import NewsFilter
from backend.agents.summarizer import NewsSummarizerAgent
from backend.rag.qa_chain import NewsQAChain
from backend.models.schemas import RawArticle, FilteredArticle
from datetime import datetime

def test_groq_integration():
    settings = get_settings()
    print(f"Testing Groq Integration with model: {settings.classifier_model}")
    
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key":
        print("Error: GROQ_API_KEY not set or invalid in .env")
        return

    # 1. Test Filter Agent
    print("\n--- Testing Filter Agent ---")
    # We need a dummy embedder for initialization but we won't call run() that needs it
    filter_tool = NewsFilter(
        embedder=None, 
        api_key=settings.groq_api_key,
        classifier_model=settings.classifier_model
    )
    
    try:
        category = filter_tool._classify("Pasar Saham Global Melonjak", "Indeks harga saham gabungan di berbagai bursa dunia mengalami kenaikan signifikan pagi ini...")
        print(f"Classification result: {category}")
    except Exception as e:
        print(f"Filter Agent Error: {e}")

    # 2. Test Summarizer Agent
    print("\n--- Testing Summarizer Agent ---")
    summarizer = NewsSummarizerAgent(
        api_key=settings.groq_api_key,
        model_name=settings.summarizer_model
    )
    
    test_article = FilteredArticle(
        url="https://test.com",
        title="Inovasi AI di Tahun 2026",
        content="Teknologi kecerdasan buatan terus berkembang pesat. Di tahun 2026, model bahasa besar kini mampu melakukan penalaran kompleks secara native. Hal ini membuka peluang baru di sektor medis, pendidikan, dan industri kreatif.",
        source="Test Source",
        published_at=datetime.now(),
        category="Teknologi",
        category_hint="Teknologi"
    )
    
    try:
        summary, key_points = summarizer._summarize_article(test_article)
        print(f"Summary: {summary}")
        print(f"Key Points: {key_points}")
    except Exception as e:
        print(f"Summarizer Agent Error: {e}")

    # 3. Test QA Chain (Direct LLM call)
    print("\n--- Testing QA Chain ---")
    qa_chain = NewsQAChain(
        retriever=None,
        api_key=settings.groq_api_key,
        model=settings.qa_model
    )
    
    # Mocking the prompt call since we don't have a retriever
    prompt = "Apa manfaat utama AI di tahun 2026 menurut artikel ini?"
    try:
        # We can't call answer() without a retriever, so we test the client directly if needed
        # or just assume the client works if the above passed.
        # But let's try to mock the retriever search.
        print("Skipping full QA Chain answer() test as it requires a working Qdrant instance.")
        print("Groq integration looks good if the above tests passed.")
    except Exception as e:
        print(f"QA Chain Error: {e}")

if __name__ == "__main__":
    test_groq_integration()
