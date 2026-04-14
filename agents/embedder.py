from __future__ import annotations

import time
from typing import Sequence

import google.generativeai as genai


class GeminiEmbedder:
    FALLBACK_MODELS: tuple[str, ...] = (
        "models/embedding-001",
        "models/gemini-embedding-001",
        "models/text-embedding-004",
    )

    def __init__(
        self,
        api_key: str,
        model: str = "models/embedding-001",
        output_dimensionality: int | None = None,
    ) -> None:
        self.model = self._canonical_model_name(model)
        self.output_dimensionality = output_dimensionality
        genai.configure(api_key=api_key)
        self.available_embedding_models = self._available_embedding_models()

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        last_error: Exception | None = None
        tried_models: list[str] = []

        for model_name in self._candidate_models():
            tried_models.append(model_name)
            for attempt in range(2):
                try:
                    kwargs: dict[str, object] = {
                        "model": model_name,
                        "content": text,
                        "task_type": task_type,
                    }
                    if self.output_dimensionality is not None:
                        kwargs["output_dimensionality"] = self.output_dimensionality

                    result = genai.embed_content(**kwargs)

                    embedding = result.get("embedding") if isinstance(result, dict) else None
                    if embedding is None:
                        raise RuntimeError("Embedding response tidak memiliki field 'embedding'.")

                    self.model = model_name
                    return embedding
                except Exception as exc:  # pragma: no cover - bergantung pada API eksternal
                    last_error = exc
                    message = str(exc).lower()
                    model_unavailable = (
                        "not found" in message
                        or "not supported" in message
                        or "404" in message
                    )
                    if model_unavailable:
                        break
                    if attempt < 1:
                        time.sleep(1.0)

        raise RuntimeError(
            "Gagal membuat embedding setelah mencoba model "
            f"{tried_models}. Error terakhir: {last_error}"
        )

    def embed_documents(self, docs: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(doc, task_type="retrieval_document") for doc in docs]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_text(query, task_type="retrieval_query")

    @staticmethod
    def _canonical_model_name(model_name: str) -> str:
        cleaned = model_name.strip()
        if cleaned.startswith("models/"):
            return cleaned
        return f"models/{cleaned}"

    def _available_embedding_models(self) -> list[str]:
        try:
            models = list(genai.list_models())
        except Exception:
            return []

        available: list[str] = []
        for model in models:
            methods = getattr(model, "supported_generation_methods", None) or []
            if "embedContent" in methods:
                name = getattr(model, "name", "")
                if name:
                    available.append(self._canonical_model_name(name))
        return available

    def _candidate_models(self) -> list[str]:
        candidates = [self.model, *self.FALLBACK_MODELS, *self.available_embedding_models]
        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            canonical = self._canonical_model_name(candidate)
            if canonical in seen:
                continue
            seen.add(canonical)
            unique.append(canonical)
        return unique
