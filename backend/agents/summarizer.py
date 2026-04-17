from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence

import google.generativeai as genai

from backend.agents.models import FilteredArticle
from backend.config.monitor import SystemMonitor
from google.api_core.exceptions import ResourceExhausted


SUMMARIZE_AND_EXTRACT_PROMPT = """
Kamu adalah editor berita profesional.

Ringkas artikel berikut dalam 2-3 kalimat Bahasa Indonesia yang netral.
Lalu ekstrak tepat 3 poin penting.

Judul: {title}
Konten: {content}

Kembalikan JSON valid dengan format:
{{
  "summary": "...",
  "key_points": ["poin 1", "poin 2", "poin 3"]
}}
""".strip()

HEADLINE_PROMPT = """
Berdasarkan ringkasan berita berikut, buat 1 kalimat headline utama hari ini dalam Bahasa Indonesia.
Maksimal 20 kata dan tanpa clickbait.

Data:
{digest_context}

Headline:
""".strip()


@dataclass(slots=True)
class ArticleInsight:
    url: str
    summary: str
    key_points: list[str]


class NewsSummarizerAgent:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_content_chars: int = 2000,
    ) -> None:
        self.model_name = self._canonical_model_name(model)
        self.max_content_chars = max_content_chars
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=self.model_name)

    def build_insights(self, articles: Sequence[FilteredArticle]) -> dict[str, ArticleInsight]:
        insights: dict[str, ArticleInsight] = {}
        total = len(articles)
        for idx, article in enumerate(articles, 1):
            print(f"  [>] Merangkum berita {idx}/{total}: {article.title[:50]}...")
            summary, key_points = self._summarize_article(article)
            # Safety delay diperketat (Limit 15 RPM = 1 request tiap 4 detik)
            time.sleep(5.0)
            insights[article.url] = ArticleInsight(
                url=article.url,
                summary=summary,
                key_points=key_points,
            )
        return insights

    def generate_daily_headline(self, articles: Sequence[FilteredArticle], insights: dict[str, ArticleInsight]) -> str:
        if not articles:
            return "Belum ada berita baru hari ini."

        context_lines: list[str] = []
        for article in articles[:12]:
            insight = insights.get(article.url)
            if not insight:
                continue
            context_lines.append(
                f"- [{article.category}] {article.title}: {insight.summary}"
            )

        if not context_lines:
            return f"Fokus berita hari ini didominasi kategori {articles[0].category}."

        prompt = HEADLINE_PROMPT.format(digest_context="\n".join(context_lines))
        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            headline = (response.text or "").strip()
            if headline:
                return " ".join(headline.split())
        except ResourceExhausted:
            SystemMonitor.update_usage(500)
        except Exception:
            pass

        top_category = self._top_category(articles)
        return f"Perkembangan terbaru didominasi isu {top_category} dari berbagai sumber berita."

    def _summarize_article(self, article: FilteredArticle) -> tuple[str, list[str]]:
        content = article.content[: self.max_content_chars]
        prompt = SUMMARIZE_AND_EXTRACT_PROMPT.format(
            title=article.title,
            content=content,
        )

        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            text = (response.text or "").strip()
            summary, key_points = self._parse_summary_json(text)
            if summary and len(key_points) == 3:
                return summary, key_points
        except ResourceExhausted:
            SystemMonitor.update_usage(500)
        except Exception:
            pass

        return self._fallback_summary(article.content)

    def _parse_summary_json(self, text: str) -> tuple[str, list[str]]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            data = json.loads(cleaned)
        except Exception:
            return "", []

        summary = str(data.get("summary", "")).strip()
        raw_points = data.get("key_points", [])
        if not isinstance(raw_points, list):
            raw_points = []

        key_points: list[str] = []
        for item in raw_points:
            value = str(item).strip()
            if value:
                key_points.append(value)
        key_points = key_points[:3]

        return summary, key_points

    def _fallback_summary(self, content: str) -> tuple[str, list[str]]:
        text = " ".join(content.split())
        if not text:
            return "Konten artikel tidak cukup untuk diringkas.", [
                "Konten sangat singkat",
                "Ringkasan otomatis fallback",
                "Perlu validasi manual",
            ]

        clauses = [part.strip() for part in text.replace("?", ".").replace("!", ".").split(".") if part.strip()]
        summary_parts = clauses[:2] if len(clauses) >= 2 else clauses[:1]
        summary = ". ".join(summary_parts).strip()
        if summary:
            summary += "."
        else:
            summary = text[:220].strip()

        key_points: list[str] = []
        for clause in clauses[:3]:
            key_points.append(clause[:90].strip())

        while len(key_points) < 3:
            key_points.append("Informasi tambahan belum tersedia")

        return summary, key_points[:3]

    @staticmethod
    def _canonical_model_name(model_name: str) -> str:
        cleaned = model_name.strip()
        if cleaned.startswith("models/"):
            return cleaned
        return f"models/{cleaned}"

    @staticmethod
    def _top_category(articles: Sequence[FilteredArticle]) -> str:
        counts: dict[str, int] = {}
        for article in articles:
            counts[article.category] = counts.get(article.category, 0) + 1
        return max(counts.items(), key=lambda kv: kv[1])[0]


def build_daily_digest_record(
    articles: Sequence[FilteredArticle],
    insights: dict[str, ArticleInsight],
    headline: str,
) -> dict:
    category_digests: dict[str, list[dict]] = {}
    for article in articles:
        insight = insights.get(article.url)
        if not insight:
            continue

        category_digests.setdefault(article.category, []).append(
            {
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "category": article.category,
                "published_at": article.published_at.isoformat(),
                "summary": insight.summary,
                "key_points": insight.key_points,
            }
        )

    return {
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": headline,
        "category_digests": category_digests,
    }
