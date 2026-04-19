from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Sequence

import google.generativeai as genai

from backend.agents.embedder import NewsEmbedder
from backend.agents.models import FilteredArticle, RawArticle
from backend.config.monitor import SystemMonitor
from google.api_core.exceptions import ResourceExhausted


CATEGORIES: tuple[str, ...] = (
    "Ekonomi",
    "Politik",
    "Teknologi",
    "Kesehatan",
    "Olahraga",
    "Hiburan",
    "Internasional",
    "Lingkungan",
    "Hukum",
    "Umum",
)

CLASSIFY_PROMPT = """
Klasifikasikan artikel berita berikut ke dalam SATU kategori:
[Ekonomi, Politik, Teknologi, Kesehatan, Olahraga, Hiburan, Internasional, Lingkungan, Hukum, Umum]

Judul: {title}
Konten (300 karakter pertama): {content_preview}

Jawab HANYA dengan nama kategori, tanpa penjelasan.
""".strip()


@dataclass(slots=True)
class FilterStats:
    total_input: int
    too_short_discarded: int
    duplicate_discarded: int
    passed: int


class NewsFilterAgent:
    def __init__(
        self,
        embedder: NewsEmbedder,
        api_key: str,
        classifier_model: str,
        dedup_threshold: float = 0.92,
        min_content_chars: int = 200,
    ) -> None:
        self.embedder = embedder
        self.classifier_model = self._canonical_model_name(classifier_model)
        self.dedup_threshold = dedup_threshold
        self.min_content_chars = min_content_chars
        genai.configure(api_key=api_key)

    def run(self, articles: Sequence[RawArticle]) -> tuple[list[FilteredArticle], FilterStats]:
        quality_articles = [a for a in articles if len(a.content.strip()) >= self.min_content_chars]
        too_short_discarded = len(articles) - len(quality_articles)

        unique_articles, duplicate_discarded = self._deduplicate(quality_articles)

        filtered: list[FilteredArticle] = []
        total = len(unique_articles)
        for idx, article in enumerate(unique_articles, 1):
            stats_usage = SystemMonitor.get_stats().get("gemini_usage", 0)
            print(f"  [>] [{stats_usage}/500] Mengklasifikasi berita {idx}/{total}: {article.title[:50]}...")
            category = self._classify(article.title, article.content)
            # Safety delay diperketat untuk mematuhi limit 15 RPM
            time.sleep(4.5)
            filtered.append(
                FilteredArticle(
                    url=article.url,
                    title=article.title,
                    content=article.content,
                    source=article.source,
                    published_at=article.published_at,
                    category=category,
                    category_hint=article.category_hint,
                    cluster_id=getattr(article, "cluster_id", -1),
                )
            )

        stats = FilterStats(
            total_input=len(articles),
            too_short_discarded=too_short_discarded,
            duplicate_discarded=duplicate_discarded,
            passed=len(filtered),
        )
        return filtered, stats

    def _deduplicate(self, articles: Sequence[RawArticle]) -> tuple[list[RawArticle], int]:
        if not articles:
            return [], 0

        texts = [self._dedup_text(article) for article in articles]
        try:
            vectors = self.embedder.embed_documents(texts)
        except Exception:
            # Fallback aman jika API embedding gagal: dedup exact title.
            seen_titles: set[str] = set()
            unique_exact: list[RawArticle] = []
            duplicate_discarded = 0
            for article in articles:
                key = self._normalize(article.title)
                if key in seen_titles:
                    duplicate_discarded += 1
                    continue
                seen_titles.add(key)
                unique_exact.append(article)
            return unique_exact, duplicate_discarded

        unique: list[RawArticle] = []
        unique_vecs: list[list[float]] = []
        duplicate_discarded = 0

        if len(articles) != len(vectors):
            raise RuntimeError(
                f"Mismatch data: Mendapat {len(vectors)} embedding untuk {len(articles)} artikel. "
                "Pemrosesan dihentikan untuk menjaga integritas data."
            )

        for article, vector in zip(articles, vectors, strict=True):
            is_duplicate = False
            for seen in unique_vecs:
                if self._cosine_similarity(vector, seen) > self.dedup_threshold:
                    is_duplicate = True
                    break

            if is_duplicate:
                duplicate_discarded += 1
                continue

            unique.append(article)
            unique_vecs.append(vector)

        return unique, duplicate_discarded

    def _classify(self, title: str, content: str) -> str:
        prompt = CLASSIFY_PROMPT.format(
            title=title.strip(),
            content_preview=content[:300].replace("\n", " ").strip(),
        )

        try:
            model = genai.GenerativeModel(model_name=self.classifier_model)
            response = model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            text = (response.text or "").strip()
            category = self._normalize_category(text)
            if category:
                return category
        except ResourceExhausted as e:
            error_msg = str(e)
            print(f"  [!] LIMIT GEMINI TERCAPAI: {error_msg}")
            # Deteksi otomatis jika limit harian (RPD) tercapai dari pesan Google
            if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_msg:
                SystemMonitor.update_usage(500)
                print("  [AUTO-SYNC] Mendeteksi batas harian 500 telah tercapai.")
        except Exception as e:
            print(f"  [!] Kesalahan Klasifikasi: {e}")

        return self._heuristic_category(title, content)

    @staticmethod
    def _canonical_model_name(model_name: str) -> str:
        cleaned = model_name.strip()
        if cleaned.startswith("models/"):
            return cleaned
        return f"models/{cleaned}"

    @staticmethod
    def _dedup_text(article: RawArticle) -> str:
        title = article.title.strip()
        preview = article.content[:240].replace("\n", " ").strip()
        return f"{title}\n{preview}"

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _normalize_category(self, raw: str) -> str | None:
        cleaned = raw.strip().strip('"').strip("'")
        # Handle response that accidentally returns JSON.
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                data = json.loads(cleaned)
                maybe = str(data.get("category", "")).strip()
                cleaned = maybe
            except Exception:
                return None

        for category in CATEGORIES:
            if cleaned.lower() == category.lower():
                return category
        return None

    def _heuristic_category(self, title: str, content: str) -> str:
        text = self._normalize(f"{title} {content[:1000]}")
        keyword_map: dict[str, tuple[str, ...]] = {
            "Ekonomi": ("rupiah", "ihsg", "inflasi", "suku bunga", "ekonomi", "bbm"),
            "Politik": ("dpr", "pemilu", "partai", "presiden", "menteri", "pilkada"),
            "Teknologi": ("ai", "startup", "aplikasi", "teknologi", "gadget", "siber"),
            "Kesehatan": ("kesehatan", "rumah sakit", "vaksin", "dokter", "penyakit"),
            "Olahraga": ("liga", "piala", "gol", "timnas", "olahraga", "pertandingan"),
            "Hiburan": ("film", "musik", "artis", "seleb", "hiburan", "konser"),
            "Internasional": ("amerika", "china", "eropa", "global", "internasional", "perang"),
            "Lingkungan": ("banjir", "iklim", "emisi", "lingkungan", "sampah", "hutan"),
            "Hukum": ("hakim", "pengadilan", "kejaksaan", "hukum", "korupsi", "vonis"),
        }

        for category, keywords in keyword_map.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "Umum"
