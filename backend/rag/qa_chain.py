from __future__ import annotations

from dataclasses import dataclass

import re
from groq import Groq
from backend.rag.retriever import NewsRetriever, SearchResult, build_context
from backend.config.monitor import SystemMonitor


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
        model: str = "qwen/qwen3-32b",
        default_top_k: int = 5,
        reranker: Any | None = None,
    ) -> None:
        self.retriever = retriever
        self.model_name = model.strip()
        self.default_top_k = default_top_k
        self.client = Groq(api_key=api_key)
        self.reranker = reranker

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
            reranker=self.reranker,
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
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                SystemMonitor.increment_llm_usage()
                
                raw_answer = (response.choices[0].message.content or "").strip()
                # Clean potential thinking blocks
                if "<think>" in raw_answer:
                    raw_answer = re.sub(r'<think>.*?</think>', '', raw_answer, flags=re.DOTALL).strip()
                
                answer_text = raw_answer
                break # Sukses, keluar dari loop
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit_exceeded" in error_str:
                    answer_text = "Maaf, limit API saat ini telah tercapai. Silakan coba lagi beberapa saat lagi."
                    break
                
                if attempt < max_retries - 1:
                    print(f"  [RETRY] Groq error (Attempt {attempt+1}/{max_retries}): {e}. Menunggu 2 detik...")
                    time.sleep(2)
                    continue
                answer_text = "Maaf, server AI sedang sibuk. Coba ulangi sebentar lagi."

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
        return model_name.strip()

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
