import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

try:
    print("[TEST] Importing NewsOrchestrator...")
    from backend.pipeline.orchestrator import run_pipeline
    print("[OK] Import successful!")
    
    print("[TEST] Initializing agents...")
    from backend.agents.planner import NewsPlannerAgent
    from backend.agents.researcher import NewsResearcherAgent
    from backend.agents.summarizer import NewsSummarizerAgent
    from backend.tools.scraper import NewsScraper
    print("[OK] Agents/Tools imports successful!")
    
    print("\n[SUCCESS] MAS Structure is valid.")
except Exception as e:
    print(f"\n[FAIL] Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
