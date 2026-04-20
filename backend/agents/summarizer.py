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
Kamu adalah editor berita profesional yang sangat teliti.

Ringkas artikel berikut dalam 2-3 kalimat Bahasa Indonesia yang netral.
Lalu ekstrak tepat 3 poin penting.

INSTRUKSI KETAT:
1. HANYA gunakan informasi yang ada di teks. JANGAN menambahkan pengetahuan luar (Anti-Hallucination).
2. Gunakan bahasa yang lugas dan objektif.

Judul: {title}
Konten: {content}

Kembalikan JSON valid dengan format:
{{
  "summary": "...",
  "key_points": ["poin 1", "poin 2", "poin 3"]
}}
""".strip()

HEADLINE_PROMPT = """
Kamu adalah Analis Intelijen Senior yang bertugas memberikan rangkuman strategis harian.

Berdasarkan data berita berikut, buatlah SATU kalimat "Global Headline" yang padat, informatif, dan langsung merujuk pada peristiwa atau subjek nyata yang paling signifikan. 

Kalimat tersebut HARUS:
1. Menghindari abstraksi berlebihan atau kumpulan buzzword generik.
2. Menyebutkan aktor, lokasi, atau sektor spesifik jika memungkinkan.
3. Menggunakan struktur sebab-akibat yang jelas: [Peristiwa Nyata/Tren Utama] memicu [Dampak Spesifik].
4. Profesional namun tetap mudah dipahami.
5. HANYA mengembalikan teks murni. JANGAN gunakan format markdown (seperti **teks**), JANGAN gunakan label seperti "Global Headline:", dan JANGAN gunakan tanda kutip di awal dan akhir kalimat.

Contoh Output yang BENAR: Ketegangan geopolitik di Selat Hormuz memicu lonjakan harga minyak global dan ketidakpastian rantai pasok energi.
Contoh Output yang SALAH: **Global Headline:** "Ketegangan geopolitik di Selat Hormuz memicu lonjakan harga minyak global."

Data:
{digest_context}

Global Headline:
""".strip()

BATCH_NAMING_PROMPT = """
Berdasarkan daftar berita di bawah ini, berikan NAMA TOPIK (2-5 kata) untuk setiap klaster.

INSTRUKSI KHUSUS:
1. Judul harus spesifik, deskriptif, dan merujuk pada subjek nyata/peristiwa (Bukan abstrak).
2. HINDARI kata-kata klise/abstrak: "Dinamika Global", "Jendela Waktu", "Langkah Strategis", "Tantangan Baru".
3. CONTOH BAGUS: "Krisis Logistik Selat Hormuz", "Akuisisi Startup AI X", "Lonjakan Harga Minyak Dunia".

Daftar Klaster:
{clusters_data}

Kembalikan HANYA dalam format JSON:
[
  {{"id": 0, "name": "..."}},
  {{"id": 1, "name": "..."}}
]
""".strip()

STORY_SYNTHESIS_PROMPT = """
Kamu adalah analis intelijen berita senior yang fokus pada efisiensi informasi.
Tugas kamu adalah memberikan "Intelligence Brief" yang sangat padat dan fokus pada dampak nyata.

INSTRUKSI KETAT:
1. Singkat & Padat: Max 15-20 kata per poin.
2. Fokus Dampak: Langsung ke info penting, jangan gunakan kalimat pembuka yang basa-basi.
3. ANTI-HALUSINASI: Jangan tambahkan angka atau proyeksi yang tidak ada di sumber berita.

Kembalikan respon JSON:
{{
  "synthesis": ["poin 1 penting", "poin 2 penting", "poin 3 penting"],
  "impact_level": "HIGH" | "MEDIUM" | "LOW",
  "impact_reason": "Alasan singkat (1 kalimat)."
}}

Kriteria Impact:
- HIGH: Disrupsi sistemik, konflik aktif, atau kebijakan nasional krusial.
- MEDIUM: Pergeseran industri signifikan atau isu regional penting.
- LOW: Update rutin tanpa efek domino besar.

Daftar Berita:
{summaries}

Intelligence Brief:
""".strip()

CORRELATION_PROMPT = """
Kamu adalah Ahli Analisis Multidisipliner (Geopolitik, Ekonomi, Teknologi, Sosial, dan Lingkungan). 
Tugas kamu adalah menemukan "Strategic Correlation" (kaitan lintas sektor) antar berbagai isu berita yang terjadi hari ini.

Tinjau daftar topik berita berikut:
{stories_summary}

Temukan kaitan strategis yang menjelaskan bagaimana satu topik bisa mempengaruhi sektor lainnya. Contoh: Bagaimana isu teknologi berdampak pada ekonomi, atau bagaimana isu lingkungan memicu pergeseran geopolitik.

Format JSON valid:
{{
  "correlations": [
    {{
      "title": "Judul Kaitan Lintas Sektor (Singkat)",
      "analysis": "Penjelasan mendalam kaitan antar isu tersebut dari berbagai sudut pandang."
    }}
  ]
}}

Pastikan analisis Anda tajam, tidak generik, dan menunjukkan pemahaman mendalam tentang hubungan sebab-akibat antar sektor.
""".strip()


@dataclass(slots=True)
class ArticleInsight:
    summary: str
    key_points: list[str]


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

    def generate_daily_headline(
        self, 
        articles: Sequence[FilteredArticle], 
        insights: dict[str, ArticleInsight],
        story_syntheses: dict[int, dict] | None = None,
        trending_map: dict[int, str] | None = None
    ) -> str:
        if not articles:
            return "Belum ada berita baru hari ini."

        context_lines: list[str] = []
        
        # PRIORITAS: Gunakan sintesis cerita yang sudah jadi agar headline lebih padat intelijen
        if story_syntheses and trending_map:
            for cid, data in story_syntheses.items():
                topic_name = trending_map.get(cid, "Topik Utama")
                # Handle both old list format and new dict format for robustness
                points = data if isinstance(data, list) else data.get("synthesis", [])
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
                    # Bersihkan label umum dan markdown jika AI tetap mengembalikannya
                    clean_headline = headline.replace("**Global Headline:**", "").replace("Global Headline:", "")
                    clean_headline = clean_headline.replace("**Headline:**", "").replace("Headline:", "")
                    clean_headline = clean_headline.replace("**", "").replace("*", "") # Hapus bolding
                    clean_headline = clean_headline.strip('"').strip("'").strip()
                    return " ".join(clean_headline.split())
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


    def build_insights(self, articles: Sequence[FilteredArticle]) -> dict[str, ArticleInsight]:
        """
        Builds insights for a list of articles, but optimizes by only 
        summarizing a representative for each cluster.
        """
        insights: dict[str, ArticleInsight] = {}
        
        # 1. Group by Cluster
        clusters: dict[int, list[FilteredArticle]] = {}
        for a in articles:
            cid = getattr(a, "cluster_id", -1)
            clusters.setdefault(cid, []).append(a)
        
        # 2. Process each cluster
        for cid, group in clusters.items():
            if cid == -1:
                # For non-clustered news, summarize all (they are unique)
                for article in group:
                    summary, key_points = self._summarize_article(article)
                    insights[article.url] = ArticleInsight(summary, key_points)
                    time.sleep(1.0)
                continue
            
            # For clustered news, pick a representative
            # Sort by content length reverse
            group.sort(key=lambda x: len(x.content), reverse=True)
            representative = group[0]
            
            print(f"  [PROCESS] Meringkas perwakilan klaster {cid}: {representative.title[:50]}...")
            summary, key_points = self._summarize_article(representative)
            rep_insight = ArticleInsight(summary, key_points)
            
            # Apply to all articles in this cluster to save API calls
            for article in group:
                insights[article.url] = rep_insight
            
            # Small delay
            time.sleep(1.5)
            
        return insights

    def generate_trending_topics(self, clusters: list[list[RawHeadline]], top_k: int = 5) -> list[str]:
        """
        Names the top K clusters using the LLM in a single BATCH call.
        """
        # Name any cluster that has articles, prioritizing trends (>1)
        potential_trending = [c for c in clusters if len(c) > 0][:top_k]

        if not potential_trending:
            return []

        print(f"  [PROCESS] Menamai {len(potential_trending)} topik tren utama dalam mode BATCH...")
        
        clusters_info = []
        for i, cluster in enumerate(potential_trending):
            titles = " | ".join([h.title for h in cluster[:4]])
            clusters_info.append(f"ID: {i} | Berita: {titles}")
        
        prompt = BATCH_NAMING_PROMPT.format(clusters_data="\n".join(clusters_info))
        
        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            
            raw_text = (response.text or "").strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            
            results = json.loads(raw_text)
            names = ["" for _ in range(len(potential_trending))]
            for res in results:
                idx = res.get("id")
                name = res.get("name", "").strip().strip('"').strip("'")
                if idx is not None and 0 <= idx < len(names):
                    names[idx] = name
            
            # Fill empty names with fallbacks
            final_names = []
            for i, name in enumerate(names):
                if name:
                    final_names.append(name)
                else:
                    # Fallback to category hint or first title
                    fallback = potential_trending[i][0].category_hint or "Topik Terkait"
                    final_names.append(fallback)
            
            return final_names
            
        except Exception as e:
            print(f"  [!] Gagal menamai topik secara batch: {e}. Menggunakan nama kategori sebagai fallback.")
            return [c[0].category_hint or "Isu Terkini" for c in potential_trending]

    def synthesize_story(self, articles: list[FilteredArticle], insights: dict[str, ArticleInsight]) -> dict:
        """
        Synthesizes multiple articles in a cluster into a set of intelligence bullet points and impact levels.
        Returns: {"synthesis": list[str], "impact_level": str, "impact_reason": str}
        """
        if not articles:
            return {}

        context = []
        for art in articles:
            insight = insights.get(art.url)
            if insight:
                context.append(f"- {art.title}: {insight.summary}")
        
        if not context:
            return {
                "synthesis": ["Informasi detail belum tersedia untuk tren ini."],
                "impact_level": "LOW",
                "impact_reason": "Data sumber tidak mencukupi untuk analisis mendalam."
            }

        prompt = STORY_SYNTHESIS_PROMPT.format(summaries="\n".join(context))
        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            
            raw_text = response.text or ""
            # Bersihkan markdown jika ada
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(raw_text)
            
            # Validasi struktur
            synthesis = data.get("synthesis", [])[:3]
            while len(synthesis) < 3:
                synthesis.append("Informasi intelijen tambahan sedang diproses.")
            
            return {
                "synthesis": synthesis,
                "impact_level": data.get("impact_level", "LOW").upper(),
                "impact_reason": data.get("impact_reason", "Tidak ada alasan spesifik yang diberikan.")
            }
                
        except Exception as e:
            print(f"  [!] Kesalahan sintesis (Detail: {str(e)}). Response: {raw_text[:200] if 'raw_text' in locals() else 'None'}")

        # --- HEURISTIC FALLBACK ---
        return {
            "synthesis": [a.title for a in articles[:3]],
            "impact_level": "LOW",
            "impact_reason": "Analisis otomatis gagal, beralih ke representasi judul berita."
        }

    def generate_correlations(self, stories: list[dict]) -> list[dict]:
        """
        Connects the dots between different top stories.
        """
        if len(stories) < 2:
            return []

        summary_list = []
        for s in stories[:6]: # Ambil top 6 cerita untuk dikorelasikan
            summary_list.append(f"Topik: {s['title']} (Dampak: {s.get('impact_level', 'LOW')}) - {s['synthesis'][0] if s['synthesis'] else ''}")
        
        prompt = CORRELATION_PROMPT.format(stories_summary="\n".join(summary_list))
        try:
            response = self.model.generate_content(prompt)
            SystemMonitor.increment_gemini_usage()
            
            raw_text = response.text or ""
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(raw_text)
            return data.get("correlations", [])[:2]
        except Exception as e:
            print(f"  [!] Gagal membuat korelasi strategis: {e}")
            return []
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
    story_syntheses: dict[int, dict] | None = None,
    trending_topics: dict[int, str] | None = None,
    correlations: list[dict] | None = None,
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
        for cid, synthesis_data in story_syntheses.items():
            if cid in clusters:
                group_articles = clusters[cid]
                # Sort articles by published_at
                group_articles.sort(key=lambda x: x["published_at"], reverse=True)
                
                impact_level = synthesis_data.get("impact_level", "LOW").upper()
                report_count = len(group_articles)
                
                # ADVANCED RANKING SCORE
                # Impact: HIGH(100), MEDIUM(50), LOW(10)
                # Volume: +1 per report (capped at 50)
                impact_weight = {"HIGH": 100, "MEDIUM": 50, "LOW": 10}
                rank_score = impact_weight.get(impact_level, 0) + min(report_count, 50)

                story_groups.append({
                    "id": cid,
                    "title": trending_topics.get(cid, "Topik Terkait"),
                    "synthesis": synthesis_data.get("synthesis", []),
                    "impact_level": impact_level,
                    "impact_reason": synthesis_data.get("impact_reason", ""),
                    "articles": group_articles[:5],
                    "total_reports": report_count,
                    "rank_score": rank_score
                })

    # --- ELITE RANKING & SLICING ---
    story_groups.sort(key=lambda x: x["rank_score"], reverse=True)
    
    top_stories = story_groups[:5]
    overflow_stories = story_groups[5:]
    
    # Redirect overflow to 'Supplemental Updates'
    if overflow_stories:
        supplemental = other_news.setdefault("Perkembangan Lainnya", [])
        for story in overflow_stories:
            # Pick the best article as a representative for 'other_news'
            rep = story["articles"][0]
            # Match the other_news structure
            supplemental.append(rep)

    return {
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": headline,
        "top_stories": top_stories,
        "correlations": correlations or [],
        "other_news": other_news,
    }
