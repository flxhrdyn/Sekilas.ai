import os
from pathlib import Path
from backend.config.settings import get_settings

def debug():
    settings = get_settings()
    print(f"ROOT_DIR: {settings.ROOT_DIR if hasattr(settings, 'ROOT_DIR') else 'Unknown'}")
    print(f"HF_HOME from settings: {settings.hf_home}")
    print(f"HF_HOME in os.environ: {os.environ.get('HF_HOME')}")
    
    # Check if folder actually exists
    if settings.hf_home:
        path = Path(settings.hf_home)
        if not path.is_absolute():
            from backend.config.settings import ROOT_DIR
            path = (ROOT_DIR / path).resolve()
        print(f"Resolved HF_HOME path: {path}")
        print(f"Path exists? {path.exists()}")

if __name__ == "__main__":
    debug()
