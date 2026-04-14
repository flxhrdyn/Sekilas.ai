from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    qdrant_url: str = Field(..., alias="QDRANT_URL")
    qdrant_api_key: str = Field(..., alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="sekilas_ai", alias="QDRANT_COLLECTION")

    embedding_model: str = Field(default="models/gemini-embedding-001", alias="EMBEDDING_MODEL")
    embedding_output_dim: int | None = Field(default=None, alias="EMBEDDING_OUTPUT_DIM")
    classifier_model: str = Field(default="models/gemini-2.0-flash", alias="CLASSIFIER_MODEL")
    summarizer_model: str = Field(default="models/gemini-2.0-flash", alias="SUMMARIZER_MODEL")
    dedup_threshold: float = Field(default=0.92, alias="DEDUP_THRESHOLD")
    min_content_chars: int = Field(default=200, alias="MIN_CONTENT_CHARS")
    summary_max_content_chars: int = Field(default=2000, alias="SUMMARY_MAX_CONTENT_CHARS")

    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")
    user_agent: str = Field(
        default="sekilas-ai-agentic-rag/0.1 (+https://github.com)",
        alias="USER_AGENT",
    )
    enable_telegram_notify: bool = Field(default=False, alias="ENABLE_TELEGRAM_NOTIFY")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")
    dashboard_url: str = Field(default="", alias="DASHBOARD_URL")

    sources_file: Path = Field(default=ROOT_DIR / "config" / "sources.yaml")
    processed_urls_file: Path = Field(default=ROOT_DIR / "data" / "processed_urls.txt")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
