import json
from datetime import datetime, UTC
from pathlib import Path
from backend.config.settings import ROOT_DIR

DATA_DIR = ROOT_DIR / "data"
STATS_FILE = DATA_DIR / "system_stats.json"

class SystemMonitor:
    @staticmethod
    def _load_stats() -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not STATS_FILE.exists():
            return {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 0}
        
        try:
            stats = json.loads(STATS_FILE.read_text(encoding="utf-8"))
            # Reset if it's a new day
            current_date = datetime.now(UTC).strftime("%Y-%m-%d")
            if stats.get("date") != current_date:
                return {"date": current_date, "gemini_usage": 0}
            return stats
        except Exception:
            return {"date": datetime.now(UTC).strftime("%Y-%m-%d"), "gemini_usage": 0}

    @staticmethod
    def _save_stats(stats: dict):
        STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    @classmethod
    def increment_gemini_usage(cls):
        stats = cls._load_stats()
        stats["gemini_usage"] = stats.get("gemini_usage", 0) + 1
        cls._save_stats(stats)

    @classmethod
    def update_usage(cls, count: int):
        stats = cls._load_stats()
        stats["gemini_usage"] = count
        cls._save_stats(stats)

    @classmethod
    def get_stats(cls) -> dict:
        from backend.config.settings import get_settings
        settings = get_settings()
        stats = cls._load_stats()
        stats["model_name"] = settings.classifier_model.split("/")[-1]
        return stats
