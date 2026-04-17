from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


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

    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    embedding_output_dim: int | None = Field(default=1024, alias="EMBEDDING_OUTPUT_DIM")
    classifier_model: str = Field(default="models/gemini-3.1-flash-lite-preview", alias="CLASSIFIER_MODEL")
    summarizer_model: str = Field(default="models/gemini-3.1-flash-lite-preview", alias="SUMMARIZER_MODEL")
    qa_model: str = Field(default="models/gemini-3.1-flash-lite-preview", alias="QA_MODEL")
    qa_top_k: int = Field(default=5, alias="QA_TOP_K")
    max_per_source: int = Field(default=8, alias="MAX_PER_SOURCE")
    dedup_threshold: float = Field(default=0.92, alias="DEDUP_THRESHOLD")
    min_content_chars: int = Field(default=200, alias="MIN_CONTENT_CHARS")
    summary_max_content_chars: int = Field(default=3000, alias="SUMMARY_MAX_CONTENT_CHARS")

    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")
    user_agent: str = Field(
        default="sekilas-ai-agentic-rag/0.1 (+https://github.com)",
        alias="USER_AGENT",
    )
    enable_telegram_notify: bool = Field(default=False, alias="ENABLE_TELEGRAM_NOTIFY")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")
    dashboard_url: str = Field(default="", alias="DASHBOARD_URL")
    hf_home: str | None = Field(default=None, alias="HF_HOME")

    sources_file: Path = Field(default=ROOT_DIR / "backend" / "config" / "sources.yaml")
    processed_urls_file: Path = Field(default=ROOT_DIR / "data" / "processed_urls.txt")
    summaries_file: Path = Field(default=ROOT_DIR / "data" / "summaries.json")

    @field_validator(
        "embedding_output_dim",
        "dedup_threshold",
        "min_content_chars",
        "summary_max_content_chars",
        "request_timeout_seconds",
        "enable_telegram_notify",
        mode="before",
    )
    @classmethod
    def _coerce_empty_to_default(cls, value: object, info: ValidationInfo) -> object:
        defaults: dict[str, object] = {
            "embedding_output_dim": 1024,
            "dedup_threshold": 0.92,
            "min_content_chars": 200,
            "summary_max_content_chars": 3000,
            "request_timeout_seconds": 20.0,
            "enable_telegram_notify": False,
        }

        if isinstance(value, str):
            cleaned = value.strip()
            empty_like = {"", '""', "''", "none", "null", "None", "NULL"}
            if cleaned.lower() in {"none", "null"}:
                cleaned = cleaned.lower()
            if cleaned in empty_like:
                return defaults.get(info.field_name, value)

            # Normalisasi string bool agar parsing konsisten lintas environment.
            if info.field_name == "enable_telegram_notify":
                lowered = cleaned.lower()
                if lowered in {"1", "true", "yes", "on"}:
                    return True
                if lowered in {"0", "false", "no", "off"}:
                    return False

            return cleaned

        if value is None:
            return defaults.get(info.field_name, value)
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if settings.hf_home:
        # Resolve path relative to ROOT_DIR if it's a relative path
        path = Path(settings.hf_home)
        if not path.is_absolute():
            path = (ROOT_DIR / path).resolve()
        os.environ["HF_HOME"] = str(path)
    return settings
