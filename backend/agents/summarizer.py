from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence

import google.generativeai as genai

from backend.agents.models import FilteredArticle, RawHeadline
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
Kamu adalah Analis Intelijen Senior. 
Berdasarkan ringkasan berita berikut, buatlah SATU kalimat "Global Headline" yang sangat profesional, analitis, dan memiliki bobot intelijen dalam Bahasa Indonesia.

Kalimat tersebut harus:
1. Menyintesis tren utama atau benang merah dari berita-berita paling penting.
2. Menggunakan kosakata profesional (Contoh: Geopolitik, Eskalasi, Volatilitas, Sentimen Pasar, Disrupsi).
3. Menjelaskan hubungan sebab-akibat jika memungkinkan (Contoh: "A terjadi seiring B, memicu dampak C").
4. Menghindari gaya bahasa portal berita umum atau clickbait.

Data:
{digest_context}

Global Headline:
""".strip()

NAMING_PROMPT = """
Berdasarkan daftar judul berita berikut yang berada dalam satu klaster topik, buatkan SATU nama topik yang singkat dan padat (2-4 kata) dalam Bahasa Indonesia.
Jangan gunakan titik di akhir.

Judul:
{titles}

Nama Topik:
""".strip()

STORY_SYNTHESIS_PROMPT = """
Kamu adalah analis intelijen berita senior.
Tugas kamu adalah memberikan "Intelligence Brief" singkat berdasarkan daftar berita dalam satu topik tren yang sama.

Buatlah TEPAT 3 poin bullet (Bahasa Indonesia) yang mensintesis inti permasalahan, kaitan antar berita, dan dampaknya.
Gunakan nada bicara profesional, padat, dan analitis.

Daftar Berita:
{summaries}

Intelligence Brief:
""".strip()


@dataclass(slots=True)
class SummarizedArticle:
    url: str
    title: str
    summary: str
    key_points: list[str]
    category: str
    source: str
    published_at: datetime
    cluster_id: int = -1


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
            stats_usage = SystemMonitor.get_stats().get("gemini_usage", 0)
            print(f"  [>] [{stats_usage}/500] Merangkum berita {idx}/{total}: {article.title[:50]}...")
            summary, key_points = self._summarize_article(article)
            # Safety delay diperketat (Limit 15 RPM = 1 request tiap 4 detik)
            time.sleep(5.0)
            insights[article.url] = ArticleInsight(
                url=article.url,
                summary=summary,
                key_points=key_points,
            )
        return insights

    def generate_daily_headline(
        self, 
        articles: Sequence[FilteredArticle], 
        insights: dict[str, ArticleInsight],
        story_syntheses: dict[int, list[str]] | None = None,
        trending_map: dict[int, str] | None = None
    ) -> str:
        if not articles:
            return "Belum ada berita baru hari ini."

        context_lines: list[str] = []
        
        # PRIORITAS: Gunakan sintesis cerita yang sudah jadi agar headline lebih padat intelijen
        if story_syntheses and trending_map:
            for cid, points in story_syntheses.items():
                topic_name = trending_map.get(cid, "Topik Utama")
                combined_points = " ".join(points[:1]) # Ambil poin pertama saja agar tidak terlalu panjang
                context_lines.append(f"Topik [{topic_name}]: {combined_points}")
        else:
            # Fallback ke ringkasan individu jika belum ada sintesis klaster
            for article in articles[:8]: # Kurangi jumlah artikel untuk meminimalisir safety trigger
                insight = insights.get(article.url)
                if not insight:
                    continue
                context_lines.append(
                    f"- [{article.category}] {article.title}: {insight.summary[:200]}"
                )

        if not context_lines:
            return f"Fokus berita hari ini didominasi kategori {articles[0].category}."

        prompt = HEADLINE_PROMPT.format(digest_context="\n".join(context_lines))
        
        # Jeda awal untuk menghindari limit RPM
        time.sleep(5.0)
        
        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                SystemMonitor.increment_gemini_usage()
                
                # Cek jika ada respon yang terblokir safety filter
                if not response.candidates or response.candidates[0].finish_reason == 3: # 3 = SAFETY
                    print(f"  [!] Headline terblokir safety filter (percobaan {attempt+1})")
                    continue
                
                headline = (response.text or "").strip()
                if headline:
                    return " ".join(headline.strip('"').split())
            except ResourceExhausted as e:
                error_msg = str(e)
                # Tampilkan pesan asli dari Google untuk diagnosa Ghost Limit
                print(f"  [!] ResourceExhausted (Percobaan {attempt+1}): {error_msg}")
                
                # Deteksi otomatis limit harian
                if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_msg:
                    SystemMonitor.update_usage(500)
                    print("  [AUTO-SYNC] Sinkronisasi kuota harian (500/500) berdasarkan respon Google.")
                
                if attempt == 0:
                    print("  [>] Mencoba lagi dalam 15 detik...")
                    time.sleep(15.0)
            except Exception as e:
                print(f"  [!] Kesalahan pembuatan headline (percobaan {attempt+1}): {e}")
                if attempt == 0:
                    time.sleep(5.0)

        # --- FALLBACK MANUAL YANG SPESIFIK (GANTI DINAMIKA GENERIK) ---
        if trending_map:
            top_topics = list(trending_map.values())[:3]
            if len(top_topics) > 1:
                topics_str = ", ".join(top_topics[:-1]) + f" serta {top_topics[-1]}"
            else:
                topics_str = top_topics[0]
            return f"Lanskap intelijen hari ini berpusat pada perkembangan terkait {topics_str}."
            
        top_titles = [a.title for a in articles[:2]]
        return f"Analisis hari ini menyoroti perkembangan strategis mengenai {', '.join(top_titles)}."


    def generate_trending_topics(self, clusters: list[list[RawHeadline]], top_k: int = 5) -> list[str]:
        """
        Names the top K clusters using the LLM to identify the overarching theme.
        """
        trends: list[str] = []
        # Only name clusters that have more than 1 article (actual trends)
        potential_trending = [c for c in clusters if len(c) > 1][:top_k]

        if not potential_trending:
            return []

        print(f"[PROCESS] Menamai {len(potential_trending)} topik tren utama hari ini...")
        for cluster in potential_trending:
            titles = "\n".join([f"- {h.title}" for h in cluster[:5]])
            prompt = NAMING_PROMPT.format(titles=titles)
            try:
                response = self.model.generate_content(prompt)
                SystemMonitor.increment_gemini_usage()
                name = (response.text or "").strip().strip('"').strip("'").strip(".")
                if name:
                    trends.append(name)
                # Small delay to respect rate limits
                time.sleep(2.0)
            except Exception as e:
                print(f"  [!] Gagal menamai topik: {e}")
                continue

        return trends

    def synthesize_story(self, articles: list[FilteredArticle], insights: dict[str, ArticleInsight]) -> list[str]:
        """
        Synthesizes multiple articles in a cluster into a set of intelligence bullet points.
        """
        if not articles:
            return []

        context = []
        for art in articles:
            insight = insights.get(art.url)
            if insight:
                context.append(f"- {art.title}: {insight.summary}")
        
        if not context:
            return ["Informasi detail belum tersedia untuk tren ini."]

        prompt = STORY_SYNTHESIS_PROMPT.format(summaries="\n".join(context))
        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            
            raw_text = response.text or ""
            # Robust bullet point extraction
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            points = []
            for line in lines:
                # Look for lines starting with typical bullet markers
                if line.startswith(("- ", "* ", "1. ", "2. ", "3. ")):
                    clean_point = line.lstrip("- *0123456789.").strip()
                    if clean_point:
                        points.append(clean_point)
            
            # Fallback for non-bulleted responses: take first 3 sentences/short paragraphs
            if not points:
                points = [l for l in lines if len(l) > 30][:3]

            if points:
                return points[:3]
                
        except Exception as e:
            print(f"  [!] Kesalahan sintesis: {str(e)}")

        # --- HEURISTIC FALLBACK (If AI fails or limit reached) ---
        # Take the titles or first key points of the first few articles in the cluster
        fallback_points = []
        for article in articles[:3]:
            # Use the headline as a bullet point if synthesis failed
            fallback_points.append(article.title)
        
        if not fallback_points:
            return ["Informasi intelijen untuk topik ini sedang diproses."]
            
        return fallback_points[:3]

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
        except ResourceExhausted as e:
            error_msg = str(e)
            print(f"  [!] LIMIT GEMINI TERCAPAI: {error_msg}")
            # Deteksi otomatis jika limit harian (RPD) tercapai dari pesan Google
            if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_msg:
                SystemMonitor.update_usage(500)
                print("  [AUTO-SYNC] Mendeteksi batas harian 500 telah tercapai.")
        except Exception as e:
            print(f"  [!] Gagal memproses artikel {article.title[:30]}: {e}")

        return self._fallback_summary(article.content)

    def _parse_summary_json(self, text: str) -> tuple[str, list[str]]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            data = json.loads(cleaned)
        except Exception as e:
            print(f"  [!] Gagal parsing JSON Ringkasan: {e}")
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
    story_syntheses: dict[int, list[str]] | None = None,
    trending_topics: dict[int, str] | None = None,
) -> dict:
    """
    Builds a story-first intelligence record.
    Articles are grouped by cluster_id into 'top_stories'.
    Articles with cluster_id == -1 or not in top_k clusters go to 'other_news'.
    """
    story_groups: list[dict] = []
    other_news: dict[str, list[dict]] = {}
    
    # Track which IDs have synthesis (Top Stories)
    top_cluster_ids = set(story_syntheses.keys()) if story_syntheses else set()
    
    # Temporary mapping for grouping
    clusters: dict[int, list[dict]] = {}

    for article in articles:
        insight = insights.get(article.url)
        if not insight:
            continue

        cid = getattr(article, "cluster_id", -1)
        item = {
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "category": article.category,
            "published_at": article.published_at.isoformat(),
            "summary": insight.summary,
            "key_points": insight.key_points,
            "cluster_id": cid,
        }

        if cid in top_cluster_ids:
            clusters.setdefault(cid, []).append(item)
        else:
            # Group by category and then by cluster to select representative later
            cat_news = other_news.setdefault(article.category, [])
            cat_news.append(item)

    # --- NOISE REDUCTION / GROUPING FOR OTHER NEWS ---
    for category in list(other_news.keys()):
        news_list = other_news[category]
        # Group these by cluster_id internally
        grouped_by_cid: dict[int, list[dict]] = {}
        for item in news_list:
            grouped_by_cid.setdefault(item["cluster_id"], []).append(item)
        
        # Select best representative for each group in this category
        summarized_list = []
        for cid_group in grouped_by_cid.values():
            # In other_news, we just show the most recent/best article for that cluster
            cid_group.sort(key=lambda x: x["published_at"], reverse=True)
            summarized_list.append(cid_group[0])
        
        # Sort category news by date
        summarized_list.sort(key=lambda x: x["published_at"], reverse=True)
        # Limit noise: if it's too many individual items, just show top 5 per category
        other_news[category] = summarized_list[:5]

    # Build Top Stories
    if story_syntheses and trending_topics:
        for cid, synthesis in story_syntheses.items():
            if cid in clusters:
                story_groups.append({
                    "id": cid,
                    "title": trending_topics.get(cid, "Topik Terkait"),
                    "synthesis": synthesis,
                    "articles": clusters[cid],
                })

    return {
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": headline,
        "top_stories": story_groups,
        "other_news": other_news,
    }
