from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence

from groq import Groq
from backend.utils.llm_utils import extract_json
from backend.models.schemas import FilteredArticle, RawHeadline
from backend.config.monitor import SystemMonitor


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
Kamu adalah Pemimpin Redaksi Senior yang bertugas menyusun "Global Headline" (Satu kalimat isu utama hari ini).

Tugas Anda adalah membaca daftar topik berita hari ini yang sudah diurutkan berdasarkan tingkat dampaknya (dari yang paling berdampak hingga yang penting lainnya), lalu buatlah SATU kalimat headline utama yang padat, informatif, dan secara akurat menggambarkan ISU UTAMA hari ini agar pembaca langsung mengetahui apa fokus terbesar hari ini.

INSTRUKSI UTAMA:
1. ISU UTAMA TIDAK HARUS GEOPOLITIK. Fokuslah pada berita yang PALING BERDAMPAK NYATA saat ini (bisa berupa Ekonomi Makro/Nasional, Kesehatan Masyarakat, Kebijakan Publik, Disrupsi Teknologi, Hukum, atau Internasional).
2. Prioritaskan topik yang berlabel [UTAMA / PALING BERDAMPAK] sebagai jangkar utama headline.
3. Hubungkan isu utama tersebut dengan berita atau topik berdampak lainnya HANYA JIKA terdapat kaitan logis yang nyata (seperti hubungan sebab-akibat, efek domino, atau pengaruh lintas sektor). Jika tidak ada kaitan logis, JANGAN dipaksakan; fokuslah menyusun satu kalimat yang tajam, spesifik, dan mendalam khusus untuk isu utama tersebut.
4. Kalimat HARUS menghindari bahasa abstrak, klise, atau buzzword generik. Sebutkan subjek, aktor, lokasi, atau sektor riil secara spesifik agar pembaca langsung tahu masalah riilnya.
5. HANYA mengembalikan teks murni. JANGAN gunakan format markdown (seperti **teks**), JANGAN gunakan label seperti "Global Headline:", dan JANGAN gunakan tanda kutip di awal dan akhir kalimat.

Contoh Output yang BENAR (Ekonomi/Domestik & Hubungannya dengan Isu Lain):
Presiden menyoroti manipulasi harga bahan pokok oleh spekulan di tengah melemahnya nilai tukar rupiah, memicu langkah tegas penertiban pasar domestik guna menekan laju inflasi.

Contoh Output yang BENAR (Kesehatan/Regulasi - Tanpa Kaitan Isu Lain):
Temuan BPOM mengenai 22 merek kopi herbal berbahaya pemicu stroke mendesak pengetatan regulasi peredaran suplemen kesehatan nasional.

Contoh Output yang BENAR (Geopolitik/Internasional & Hubungannya dengan Isu Lain):
Aksi protes warga Greenland menolak pembukaan konsulat baru AS di Nuuk menghambat rencana ekspansi diplomatik Washington di Artik demi mengamankan jalur logistik baru.

Data Berita Terurut:
{digest_context}

Global Headline (Gunakan Bahasa Indonesia):
""".strip()

BATCH_NAMING_PROMPT = """
Berdasarkan daftar berita di bawah ini, berikan NAMA TOPIK (2-5 kata) untuk setiap klaster.

INSTRUKSI KHUSUS:
1. Judul harus spesifik, deskriptif, dan merujuk pada subjek nyata/peristiwa (Bukan abstrak).
2. HINDARI kata-kata generik: "Internasional", "Nasional", "Politik", "Ekonomi", "Berita", "Update".
3. HINDARI kata klise: "Dinamika Global", "Langkah Strategis", "Tantangan Baru".
4. CONTOH BAGUS: "Konflik Perbatasan Israel-Lebanon", "Sertifikasi Halal Produk Sanex", "Pilihan Karir Guru Piano di Singapura".
5. WAJIB menggunakan Bahasa Indonesia yang formal.

Daftar Klaster:
{clusters_data}

Kembalikan HANYA dalam format JSON object:
{{
  "topics": [
    {{"id": 0, "name": "..."}},
    {{"id": 1, "name": "..."}}
  ]
}}
""".strip()

STORY_SYNTHESIS_PROMPT = """
Kamu adalah analis intelijen berita senior yang fokus pada efisiensi informasi.
Tugas kamu adalah memberikan "Intelligence Brief" yang sangat padat dan fokus pada dampak nyata.

INSTRUKSI KETAT:
1. Singkat & Padat: Max 15-20 kata per poin.
2. Fokus Dampak: Langsung ke info penting, jangan gunakan kalimat pembuka yang basa-basi.
3. ANTI-HALUSINASI: Jangan tambahkan angka atau proyeksi yang tidak ada di sumber berita.
4. Gunakan Bahasa Indonesia yang ringkas dan profesional.

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

Daftar Berita Utama:
{summaries}

Konteks Riset Tambahan (Jika ada):
{research_context}

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
Seluruh respon HARUS dalam Bahasa Indonesia.
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
        model_name: str,
        max_content_chars: int = 2000,
    ) -> None:
        self.model_name = model_name.strip()
        self.max_content_chars = max_content_chars
        self.client = Groq(api_key=api_key)

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
            # Hitung volume artikel per klaster untuk menentukan skor pemeringkatan
            cluster_counts = {}
            for art in articles:
                cid = getattr(art, "cluster_id", -1)
                if cid != -1:
                    cluster_counts[cid] = cluster_counts.get(cid, 0) + 1
            
            # Hitung skor pemeringkatan awal agar kita tahu mana yang paling berdampak
            impact_weight = {"HIGH": 100, "MEDIUM": 50, "LOW": 10}
            scored_stories = []
            for cid, data in story_syntheses.items():
                topic_name = trending_map.get(cid, "Topik")
                impact_level = data.get("impact_level", "LOW").upper()
                report_count = cluster_counts.get(cid, len(data.get("synthesis", [])))
                
                score = impact_weight.get(impact_level, 0) + min(report_count, 50)
                scored_stories.append((score, cid, topic_name, data))
                
            # Urutkan berdasarkan skor tertinggi (dari yang paling berdampak)
            scored_stories.sort(key=lambda x: x[0], reverse=True)
            
            for i, (score, cid, topic_name, data) in enumerate(scored_stories):
                points = data if isinstance(data, list) else data.get("synthesis", [])
                combined_points = " ".join(points[:2]) # Ambil 2 poin teratas agar konteks lebih kaya
                impact = data.get("impact_level", "LOW").upper()
                
                # Berikan tanda khusus pada yang paling berdampak
                prefix = "[UTAMA / PALING BERDAMPAK]" if i == 0 else f"[PENTING / DAMPAK {impact}]"
                context_lines.append(f"{prefix} Topik '{topic_name}': {combined_points}")
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
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                SystemMonitor.increment_llm_usage()
                
                headline = (response.choices[0].message.content or "").strip()
                if headline:
                    # Clean potential markdown/thinking blocks
                    if "<think>" in headline:
                        headline = re.sub(r'<think>.*?</think>', '', headline, flags=re.DOTALL).strip()
                    
                    # Bersihkan label umum dan markdown jika AI tetap mengembalikannya
                    clean_headline = headline.replace("**Global Headline:**", "").replace("Global Headline:", "")
                    clean_headline = clean_headline.replace("**Headline:**", "").replace("Headline:", "")
                    clean_headline = clean_headline.replace("**", "").replace("*", "") # Hapus bolding
                    clean_headline = clean_headline.strip('"').strip("'").strip()
                    return " ".join(clean_headline.split())
            except Exception as e:
                print(f"  [!] Kesalahan pembuatan headline (percobaan {attempt+1}): {e}")
                if "rate_limit_exceeded" in str(e).lower():
                    print("  [>] Rate limit tercapai. Menunggu 25 detik...")
                    time.sleep(25.0)
                elif attempt == 0:
                    time.sleep(10.0)
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
            # Jeda antar klaster untuk menjaga TPM/RPM
            time.sleep(3.5)
            
        return insights

    def generate_trending_topics(self, clusters: list[list[RawHeadline]], top_k: int = 5) -> list[str]:
        """
        Names the top K clusters using the LLM in a single BATCH call with robust error handling and retries.
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
        
        # We try up to 2 attempts with exponential backoff on rate limits
        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                SystemMonitor.increment_llm_usage()
                
                raw_text = response.choices[0].message.content
                data = extract_json(raw_text)
                
                # Handle cases where it might return the list directly or inside 'topics'
                results = data.get("topics", []) if isinstance(data, dict) else data
                
                names = ["" for _ in range(len(potential_trending))]
                for res in results:
                    if not isinstance(res, dict): continue
                    idx = res.get("id")
                    name = res.get("name", "").strip().strip('"').strip("'")
                    if idx is not None and 0 <= idx < len(names):
                        names[idx] = name
                
                # Fill empty or generic names with fallbacks
                final_names = []
                for i, name in enumerate(names):
                    is_generic = name.lower() in [
                        "internasional", "nasional", "politik", "ekonomi", "kesehatan", 
                        "teknologi", "olahraga", "hiburan", "lingkungan", "hukum", "umum", 
                        "berita", "update", "topik terkait", "topik", "isu terkini", "lifestyle",
                        "sains", "budaya", "edukasi"
                    ]
                    if name and not is_generic:
                        final_names.append(name)
                    else:
                        first_title = potential_trending[i][0].title
                        fallback = first_title[:42] + "..." if len(first_title) > 45 else first_title
                        final_names.append(fallback)
                
                return final_names
                
            except Exception as e:
                print(f"  [!] Gagal menamai topik secara batch (percobaan {attempt+1}): {e}")
                if "rate_limit_exceeded" in str(e).lower():
                    print("  [>] Rate limit tercapai. Menunggu 25 detik...")
                    time.sleep(25.0)
                elif attempt == 0:
                    time.sleep(10.0)
        
        # --- ULTIMATE FALLBACK: Use first article title from each cluster ---
        print("  [!] Semua percobaan batch naming gagal. Menggunakan judul berita pertama sebagai fallback.")
        final_fallbacks = []
        for cluster in potential_trending:
            first_title = cluster[0].title
            fallback = first_title[:42] + "..." if len(first_title) > 45 else first_title
            final_fallbacks.append(fallback)
        return final_fallbacks

    def synthesize_story(self, articles: list[FilteredArticle], insights: dict[str, ArticleInsight], external_context: list[dict] = None) -> dict:
        """
        Synthesizes multiple articles in a cluster into a set of intelligence bullet points and impact levels.
        Optional external_context from Researcher Agent can be provided.
        Returns: {"synthesis": list[str], "impact_level": str, "impact_reason": str}
        """
        if not articles:
            return {}

        context = []
        for art in articles:
            insight = insights.get(art.url)
            if insight:
                context.append(f"- {art.title}: {insight.summary}")
        
        research_str = ""
        if external_context:
            research_str = "\n".join([f"- {res.get('title')}: {res.get('content')[:500]}" for res in external_context])
        else:
            research_str = "Tidak ada riset eksternal tambahan."

        if not context:
            return {
                "synthesis": ["Informasi detail belum tersedia untuk tren ini."],
                "impact_level": "LOW",
                "impact_reason": "Data sumber tidak mencukupi untuk analisis mendalam."
            }

        prompt = STORY_SYNTHESIS_PROMPT.format(
            summaries="\n".join(context),
            research_context=research_str
        )
        
        time.sleep(5.0) # Throttling proaktif
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            SystemMonitor.increment_llm_usage()
            
            raw_text = response.choices[0].message.content
            data = extract_json(raw_text)
            
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
        
        time.sleep(5.0) # Throttling proaktif
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            SystemMonitor.increment_llm_usage()
            
            raw_text = response.choices[0].message.content
            data = extract_json(raw_text)
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

        # Jeda proaktif untuk menjaga kuota TPM agar tidak cepat habis (Throttling)
        time.sleep(5.0)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            SystemMonitor.increment_llm_usage()
            text = response.choices[0].message.content
            summary, key_points = self._parse_summary_json(text)
            if summary and len(key_points) == 3:
                return summary, key_points
        except Exception as e:
            print(f"  [!] Gagal memproses artikel {article.title[:30]}: {e}")
            if "rate_limit_exceeded" in str(e).lower():
                print("  [>] Rate limit tercapai. Menunggu 20 detik...")
                time.sleep(20)
            else:
                time.sleep(2) # Jeda kecil jika error biasa

        return self._fallback_summary(article.content)

    def _parse_summary_json(self, text: str) -> tuple[str, list[str]]:
        try:
            data = extract_json(text)
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
        return model_name.strip()

    @staticmethod
    def _top_category(articles: Sequence[FilteredArticle]) -> str:
        counts: dict[str, int] = {}
        for article in articles:
            counts[article.category] = counts.get(article.category, 0) + 1
        return max(counts.items(), key=lambda kv: kv[1])[0]


def _is_topic_relevant_to_headline(topic_name: str, headline: str) -> bool:
    if not topic_name or not headline:
        return False
        
    topic_clean = topic_name.lower()
    headline_clean = headline.lower()
    
    # 1. Direct substring match (always True)
    if topic_clean in headline_clean:
        return True
        
    # 2. Key word overlap check
    # Split into words and remove punctuation
    words = [w.strip(".,;:!?()\"'") for w in topic_clean.split()]
    # Stop words in Indonesian / English to filter out noise
    stop_words = {
        "di", "oleh", "dan", "ke", "dari", "yang", "untuk", "dalam", "dengan", "pada", 
        "adalah", "sebagai", "atau", "ini", "itu", "the", "and", "for", "with", "from", "under"
    }
    
    keywords = [w for w in words if w and w not in stop_words and len(w) > 2]
    
    if not keywords:
        return False
        
    # Count matches. If a keyword matches or is partially matched (stemmed) in the headline
    match_count = 0
    for kw in keywords:
        # Check if the keyword itself is in the headline, or if a stem of it matches
        if kw in headline_clean:
            match_count += 1
        else:
            # Check partial overlap (e.g. "greenland" matches "greenlanders")
            # If the keyword starts with or contains part of a headline word
            for hw in headline_clean.split():
                clean_hw = hw.strip(".,;:!?()\"'")
                if len(clean_hw) > 2 and (clean_hw in kw or kw in clean_hw):
                    match_count += 1
                    break
                    
    # If at least 2 keywords match and match ratio is >= 30%
    if len(keywords) >= 2:
        return match_count >= 2 and (match_count / len(keywords) >= 0.3)
    else:
        return match_count >= 1


def build_daily_digest_record(
    articles: Sequence[FilteredArticle],
    insights: dict[str, ArticleInsight],
    headline: str,
    story_syntheses: dict[int, dict] | None = None,
    trending_topics: dict[int, str] | None = None,
    correlations: list[dict] | None = None,
    research_results: dict[int, list[dict]] | None = None,
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
                topic_name = trending_topics.get(cid, "Topik")
                
                base_score = impact_weight.get(impact_level, 0) + min(report_count, 50)
                
                # STRATEGIC BOOST: Jika topik ini disebutkan atau sangat relevan dengan Global Headline, 
                # berikan bonus besar agar dia naik ke urutan #1 (Cell Gede)
                strategic_bonus = 0
                if headline and _is_topic_relevant_to_headline(topic_name, headline):
                    strategic_bonus = 200 # Pastikan dia jadi nomor 1
                
                rank_score = base_score + strategic_bonus

                story_groups.append({
                    "id": cid,
                    "topic": topic_name,
                    "title": topic_name, # Alias for frontend compatibility
                    "synthesis": synthesis_data.get("synthesis", []),
                    "impact_level": impact_level,
                    "impact_reason": synthesis_data.get("impact_reason", ""),
                    "external_research": research_results.get(cid) if research_results else None,
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
        "global_headline": headline, # Alias for frontend compatibility
        "top_stories": top_stories,
        "correlations": correlations or [],
        "other_news": other_news,
    }
