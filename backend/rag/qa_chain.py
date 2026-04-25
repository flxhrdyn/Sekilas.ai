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
        model: str = "models/gemini-3.1-flash-lite-preview",
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
        import time
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

        answer_text = ""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                SystemMonitor.increment_gemini_usage()
                answer_text = (response.text or "").strip()
                break # Sukses, keluar dari loop
            except ResourceExhausted:
                answer_text = "Maaf, limit Gemini saat ini telah tercapai. Silakan coba lagi beberapa saat lagi atau besok."
                break # Limit beneran habis, tidak perlu retry
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  [RETRY] Gemini error (Attempt {attempt+1}/{max_retries}): {e}. Menunggu 2 detik...")
                    time.sleep(2)
                    continue
                answer_text = "Maaf, server Gemini sedang sibuk (Error 503). Coba ulangi sebentar lagi."

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
