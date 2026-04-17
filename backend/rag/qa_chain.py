from __future__ import annotations

from dataclasses import dataclass

import google.generativeai as genai

from backend.rag.retriever import NewsRetriever, SearchResult, build_context
from backend.config.monitor import SystemMonitor
from google.api_core.exceptions import ResourceExhausted


QA_PROMPT = """
Kamu adalah asisten berita cerdas Sekilas.ai.
Jawab pertanyaan pengguna HANYA berdasarkan konteks berita di bawah.
Jika informasi tidak ada di konteks, jawab tepat: "Informasi ini belum ada di database berita saya."
Selalu sertakan sumber berupa URL yang relevan.

Konteks berita:
{context}

Pertanyaan:
{question}

Jawaban (Bahasa Indonesia):
""".strip()


@dataclass(slots=True)
class AnswerResult:
    answer: str
    sources: list[str]
    retrieved: list[SearchResult]


class NewsQAChain:
    def __init__(
        self,
        retriever: NewsRetriever,
        api_key: str,
        model: str = "models/gemini-2.0-flash",
        default_top_k: int = 5,
    ) -> None:
        self.retriever = retriever
        self.model_name = self._canonical_model_name(model)
        self.default_top_k = default_top_k

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=self.model_name)

    def answer(
        self,
        question: str,
        top_k: int | None = None,
        category_filter: str | None = None,
    ) -> AnswerResult:
        limit = top_k if top_k is not None else self.default_top_k
        results = self.retriever.search(
            query=question,
            top_k=limit,
            category_filter=category_filter,
        )

        if not results:
            return AnswerResult(
                answer="Informasi ini belum ada di database berita saya.",
                sources=[],
                retrieved=[],
            )

        context = build_context(results)
        prompt = QA_PROMPT.format(context=context, question=question.strip())

        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            answer_text = (response.text or "").strip()
        except ResourceExhausted:
            SystemMonitor.update_usage(500)
            answer_text = "Maaf, limit harian Gemini telah tercapai (500/500). Silakan coba lagi besok."
        except Exception:
            answer_text = "Maaf, proses jawaban sedang mengalami kendala. Coba ulangi sebentar lagi."

        sources = self._unique_sources(results)
        if "http" not in answer_text and sources:
            source_block = "\n".join(f"- {url}" for url in sources[:5])
            answer_text = f"{answer_text}\n\nSumber:\n{source_block}"

        return AnswerResult(
            answer=answer_text,
            sources=sources,
            retrieved=results,
        )

    @staticmethod
    def _canonical_model_name(model_name: str) -> str:
        cleaned = model_name.strip()
        if cleaned.startswith("models/"):
            return cleaned
        return f"models/{cleaned}"

    @staticmethod
    def _unique_sources(results: list[SearchResult]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for item in results:
            if not item.url or item.url in seen:
                continue
            seen.add(item.url)
            unique.append(item.url)
        return unique
