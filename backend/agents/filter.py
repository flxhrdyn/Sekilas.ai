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

BATCH_CLASSIFY_PROMPT = """
Tentukan kategori paling tepat untuk setiap berita berikut dari daftar ini:
[Ekonomi, Politik, Teknologi, Kesehatan, Olahraga, Hiburan, Internasional, Lingkungan, Hukum, Umum]

List Berita (ID | Judul | Preview):
{news_list}

Kembalikan HANYA dalam format JSON valid:
[
  {{"id": 0, "category": "..."}},
  {{"id": 1, "category": "..."}}
]

Pastikan analisis Anda tajam dan hanya pilih satu kategori terbaik.
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
        dedup_threshold: float = 0.95,
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

        # Step 1: Local Semantic Deduplication (Grabs first representative of near-exact news)
        unique_articles, duplicate_discarded = self._deduplicate(quality_articles)

        if not unique_articles:
            return [], FilterStats(len(articles), too_short_discarded, duplicate_discarded, 0)

        # Step 2: Batch Classification (API Saver)
        print(f"  [PROCESS] Mengklasifikasi {len(unique_articles)} berita unik dalam mode BATCH...")
        
        # Split into batches of 20 to respect token limits and context clarity
        batch_size = 20
        all_categorized: dict[str, str] = {} # URL -> Category
        
        for i in range(0, len(unique_articles), batch_size):
            current_batch = unique_articles[i:i+batch_size]
            batch_results = self._classify_batch(current_batch)
            all_categorized.update(batch_results)
            # Small delay to respect RPM
            time.sleep(2.0)

        filtered: list[FilteredArticle] = []
        for article in unique_articles:
            res = all_categorized.get(article.url, {})
            # Handle both string (old format) and dict (new format) gracefully
            if isinstance(res, str):
                category = res
                is_news = True
            else:
                category = res.get("category", "Umum")
                is_news = res.get("is_news", True)
            
            # HARD FILTER: Buang jika bukan berita berkualitas/intelijen
            if not is_news:
                print(f"  [FILTERED] Membuang konten noise: {article.title[:50]}...")
                continue
                
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

    def _classify_batch(self, articles: Sequence[RawArticle]) -> dict[str, str]:
        """
        Classifies a batch of articles in a single Gemini call.
        Returns a mapping of URL -> Category.
        """
        news_list_str = []
        for idx, art in enumerate(articles):
            news_list_str.append(f"ID: {idx} | Judul: {art.title} | Preview: {art.content[:150]}")
        
        prompt = BATCH_CLASSIFY_PROMPT.format(news_list="\n".join(news_list_str))
        
        try:
            model = genai.GenerativeModel(model_name=self.classifier_model)
            response = model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            
            raw_text = (response.text or "").strip()
            # Clean JSON markers if present
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            results = json.loads(raw_text)
            url_to_res = {}
            for res in results:
                idx = res.get("id")
                cat = self._normalize_category(res.get("category", "Umum"))
                is_news = res.get("is_news", True)
                if idx is not None and 0 <= idx < len(articles):
                    url_to_res[articles[idx].url] = {
                        "category": cat or "Umum",
                        "is_news": is_news
                    }
            
            return url_to_res
            
        except Exception as e:
            print(f"  [!] Kesalahan Batch Classify: {e}. Beralih ke heuristik dasar yang ketat.")
            # Fallback to heuristics for the whole batch. 
            url_to_res = {}
            for art in articles:
                # Heuristic ketat: Konten harus cukup panjang dan tidak berisi kata kunci noise
                is_news = True
                if len(art.content) < 800:
                    is_news = False
                    
                noise_keywords = ["beli", "harga", "promo", "diskon", "jual", "toko", "belanja", "zodiak", "ramalan", "gosip"]
                if any(kw in art.content.lower() for kw in noise_keywords):
                    is_news = False
                    
                url_to_res[art.url] = {"category": self._heuristic_category(art.title, art.content), "is_news": is_news}
            return url_to_res

    def _deduplicate(self, articles: Sequence[RawArticle]) -> tuple[list[RawArticle], int]:
        if not articles:
            return [], 0

        texts = [self._dedup_text(article) for article in articles]
        try:
            vectors, _ = self.embedder.embed_documents(texts)
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
