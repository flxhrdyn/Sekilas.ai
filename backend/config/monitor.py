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
        from backend.config.settings import get_settings
        settings = get_settings()
        # Read-only operation doesn't strictly need a heavy write lock, 
        # but let's use a simple read to be safe.
        stats = cls._load_stats()
        stats["model_name"] = settings.classifier_model.split("/")[-1]
        return stats
