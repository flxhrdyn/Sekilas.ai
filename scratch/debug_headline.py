import sys
from pathlib import Path
from datetime import datetime, UTC

# Add project root to sys.path
sys.path.append(r"d:\Programming\Python\Python Projects\01_GenAI\agentic-rag-sekilas-ai")

from backend.agents.summarizer import NewsSummarizerAgent, ArticleInsight
from backend.agents.models import FilteredArticle
from backend.config.settings import get_settings

def test_headline():
    settings = get_settings()
    agent = NewsSummarizerAgent(
        api_key=settings.gemini_api_key,
        model=settings.summarizer_model
    )
    
    # Mock data
    articles = [
        FilteredArticle(
            url="url1", title="Isu Geopolitik Timur Tengah", content="...", source="...",
            published_at=datetime.now(UTC), category="Politik", category_hint="Politik", cluster_id=1
        ),
        FilteredArticle(
            url="url2", title="Harga Minyak Melonjak", content="...", source="...",
            published_at=datetime.now(UTC), category="Ekonomi", category_hint="Ekonomi", cluster_id=1
        )
    ]
    insights = {
        "url1": ArticleInsight(url="url1", summary="Eskalasi di Selat Hormuz memicu kekhawatiran geopolitik.", key_points=[]),
        "url2": ArticleInsight(url="url2", summary="Harga minyak mentah naik tajam akibat ketegangan global.", key_points=[])
    }
    
    print("Testing headline generation...")
    headline = agent.generate_daily_headline(articles, insights)
    print(f"Result: {headline}")

if __name__ == "__main__":
    test_headline()
