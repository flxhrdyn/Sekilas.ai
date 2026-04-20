import json
import portalocker
from datetime import datetime, UTC
from pathlib import Path
from backend.config.settings import ROOT_DIR

DATA_DIR = ROOT_DIR / "data"
STATS_FILE = DATA_DIR / "system_stats.json"

class SystemMonitor:
    @staticmethod
    def _load_stats(lock=None) -> dict:
        """
        Internal load function. If a lock is provided, it assumes the file is already open/locked.
        Otherwise, it performs a simple read.
        """
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not STATS_FILE.exists():
            return {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 0}
        
        try:
            content = STATS_FILE.read_text(encoding="utf-8")
            if not content.strip():
                return {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 0}
            
            stats = json.loads(content)
            # Reset if it's a new day
            current_date = datetime.now(UTC).strftime("%Y-%m-%d")
            if stats.get("date") != current_date:
                return {"date": current_date, "gemini_usage": 0}
            return stats
        except Exception:
            return {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 0}

    @staticmethod
    def _save_stats(stats: dict):
        """Atomic save using portalocker to prevent race conditions."""
        with portalocker.Lock(STATS_FILE, mode="w", encoding="utf-8", timeout=5) as f:
            json.dump(stats, f, indent=2)

    @classmethod
    def increment_gemini_usage(cls):
        """Thread-safe increment."""
        # We need a shared lock for both read and write to be truly atomic
        with portalocker.Lock(STATS_FILE, mode="r+", encoding="utf-8", timeout=5) as f:
            try:
                content = f.read()
                if not content.strip():
                    stats = {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 1}
                else:
                    stats = json.loads(content)
                    current_date = datetime.now(UTC).strftime("%Y-%m-%d")
                    if stats.get("date") != current_date:
                        stats = {"date": current_date, "gemini_usage": 1}
                    else:
                        stats["gemini_usage"] = stats.get("gemini_usage", 0) + 1
                
                # Rewind and write
                f.seek(0)
                f.truncate()
                json.dump(stats, f, indent=2)
            except Exception:
                # Fallback jika korup
                pass

    @classmethod
    def update_usage(cls, count: int):
        """Thread-safe update."""
        with portalocker.Lock(STATS_FILE, mode="r+", encoding="utf-8", timeout=5) as f:
            current_date = datetime.now(UTC).strftime("%Y-%m-%d")
            stats = {"date": current_date, "gemini_usage": count}
            f.seek(0)
            f.truncate()
            json.dump(stats, f, indent=2)

    @classmethod
    def get_stats(cls) -> dict:
        import httpx
        from backend.config.settings import get_settings
        from backend.services.news_service import NewsService
        settings = get_settings()
        
        stats = cls._load_stats()
        stats["model_name"] = settings.classifier_model.split("/")[-1]
        
        # 1. Get Pipeline Logic
        latest_digest = NewsService.get_latest_digest()
        last_synthesis = "N/A"
        if latest_digest:
            gen_at = latest_digest.get("generated_at", "")
            if "T" in gen_at:
                last_synthesis = gen_at.split("T")[1][:5]

        # 2. Real-Time Service Health Checks
        qdrant_status = "offline"
        if settings.qdrant_url:
            try:
                # Minimal probe with 1.5s timeout
                headers = {}
                if settings.qdrant_api_key:
                    headers["api-key"] = settings.qdrant_api_key
                resp = httpx.get(f"{settings.qdrant_url}/healthz", headers=headers, timeout=1.5)
                if resp.status_code in [200, 403]: # 403 means reachable but needs full auth
                    qdrant_status = "online"
            except Exception:
                qdrant_status = "offline"

        gemini_status = "online" if settings.gemini_api_key else "offline"

        stats["agents"] = [
            {"id": "scraper", "name": "News Scraper Agent", "status": "standby", "last_run": last_synthesis},
            {"id": "filter", "name": "Gatekeeper Filter", "status": "standby", "last_run": last_synthesis},
            {"id": "cluster", "name": "Discovery Cluster", "status": "standby", "last_run": last_synthesis},
            {"id": "summarizer", "name": "Intelligence Agent", "status": "standby", "last_run": last_synthesis},
            {"id": "notifier", "name": "Broadcast Notifier", "status": "standby", "last_run": last_synthesis},
            {"id": "embedder", "name": "Knowledge Embedder", "status": qdrant_status, "last_run": "Live"},
            {"id": "qa", "name": "Executive QA Agent", "status": gemini_status, "last_run": "Ready"}
        ]
        
        return stats
