# 🧠 Sekilas.ai Agentic-RAG
### An Automated Intelligence News System with Semantic Retrieval

> **Status:** Planning  
> **Target Cost:** Rp 0 / bulan  
> **Stack:** Python · LangGraph · Gemini API · Qdrant/FAISS · Streamlit  
> **Deployment:** GitHub Actions + Koyeb/Render

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Struktur Repositori](#3-struktur-repositori)
4. [Tech Stack & Justifikasi](#4-tech-stack--justifikasi)
5. [Pipeline Detail](#5-pipeline-detail)
6. [Fase Pengerjaan](#6-fase-pengerjaan)
7. [Spesifikasi Setiap Komponen](#7-spesifikasi-setiap-komponen)
8. [Konfigurasi GitHub Actions](#8-konfigurasi-github-actions)
9. [Free Tier Limits & Mitigasi](#9-free-tier-limits--mitigasi)
10. [Definisi Done (DoD)](#10-definisi-done-dod)

---

## 1. Overview

Sekilas.ai Agentic-RAG adalah sistem aggregator berita otomatis yang **memahami isi berita**, bukan sekadar mengumpulkan link. Sistem ini menggabungkan tiga paradigma AI modern:

- **Agentic AI** — AI agent bertugas aktif melakukan keputusan (filter duplikat, klasifikasi kategori, routing)
- **RAG (Retrieval-Augmented Generation)** — pencarian berbasis makna (semantik) menggunakan vector embeddings
- **Automated Pipeline** — berjalan otomatis setiap hari tanpa intervensi manual

### Nilai Utama

| Fitur | Deskripsi |
|---|---|
| Pencarian semantik | Cari "inflasi ekonomi" → temukan artikel bertopik "kenaikan harga BBM" |
| Deduplikasi otomatis | AI agent buang berita duplikat lintas sumber |
| Ringkasan harian | Digest 10 berita terpenting dikirim otomatis setiap pagi |
| Q&A berita | Tanya "Apa isu terpanas minggu ini?" → dijawab berbasis data nyata |
| Zero cost | Semua komponen menggunakan free tier yang tersedia |

---

## 2. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Actions (Cron)                  │
│              Trigger: setiap hari 07:00 WIB              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              SCRAPING AGENT (agents/scraper.py)          │
│   RSS Feeds: Kompas · Detik · CNBC · Tempo · BBC Indo   │
└──────────┬──────────────────────────────────────────────┘
           │  Raw Articles (title, url, content, source, timestamp)
           ▼
┌─────────────────────────────────────────────────────────┐
│            SMART FILTER AGENT (agents/filter.py)         │
│   - Deduplikasi berbasis cosine similarity (threshold>0.92)│
│   - Klasifikasi kategori: Ekonomi/Politik/Teknologi/dll  │
│   - Scoring relevansi artikel                            │
└──────────┬──────────────────────────────────────────────┘
           │  Clean, Classified Articles
           ├─────────────────────┐
           ▼                     ▼
┌──────────────────┐   ┌─────────────────────────────────┐
│ EMBEDDING AGENT  │   │    SUMMARIZATION AGENT           │
│ (agents/embed.py)│   │    (agents/summarizer.py)        │
│                  │   │                                   │
│ Gemini Embedding │   │ Gemini Flash / Groq Llama         │
│ text-embedding-  │   │ LangGraph workflow                │
│ 004 → vectors    │   │ → ringkasan + key points          │
└────────┬─────────┘   └──────────────┬──────────────────┘
         │                            │
         ▼                            ▼
┌──────────────────┐   ┌─────────────────────────────────┐
│  VECTOR DATABASE │   │      SUMMARY STORAGE             │
│  Qdrant Cloud    │   │      data/summaries.json         │
│  (atau FAISS     │   │      (atau Supabase free tier)   │
│   lokal .bin)    │   │                                   │
└──────────────────┘   └──────────────────────────────────┘
         │                            │
         └──────────────┬─────────────┘
                        ▼
         ┌─────────────────────────────┐
         │     DELIVERY LAYER          │
         ├──────────────┬──────────────┤
         │  NOTIFIER    │  DASHBOARD   │
         │  Telegram Bot│  Streamlit   │
         │  atau Email  │  (RAG Q&A)   │
         └──────────────┴──────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   HOSTING GRATIS      │
                  │   Koyeb / Render /    │
                  │   HuggingFace Spaces  │
                  └───────────────────────┘
```

---

## 3. Struktur Repositori

```
sekilas-ai-rag/
│
├── .github/
│   └── workflows/
│       ├── daily_pipeline.yml       # Cron job utama (07:00 WIB)
│       └── deploy_dashboard.yml     # Deploy Streamlit ke Koyeb
│
├── agents/
│   ├── __init__.py
│   ├── scraper.py                   # Scraping RSS + NewsAPI
│   ├── filter.py                    # Dedup + klasifikasi (Agentic)
│   ├── embedder.py                  # Generate vector embeddings
│   ├── summarizer.py                # Summarization dengan LangGraph
│   └── notifier.py                  # Kirim Telegram / Email
│
├── rag/
│   ├── __init__.py
│   ├── vector_store.py              # Abstraksi Qdrant / FAISS
│   ├── retriever.py                 # Semantic search
│   └── qa_chain.py                  # RAG chain untuk Q&A
│
├── dashboard/
│   ├── app.py                       # Streamlit main app
│   ├── pages/
│   │   ├── 01_Digest_Harian.py
│   │   ├── 02_Cari_Berita.py        # Semantic search UI
│   │   └── 03_Tanya_AI.py           # RAG Q&A UI
│   └── components/
│       └── news_card.py             # Reusable UI component
│
├── pipeline/
│   ├── __init__.py
│   └── orchestrator.py             # LangGraph graph definition
│
├── config/
│   ├── settings.py                  # Config management (pydantic)
│   └── sources.yaml                 # Daftar sumber berita + RSS URL
│
├── data/
│   ├── summaries.json               # Storage ringkasan harian
│   ├── faiss_index.bin              # FAISS index (jika tidak pakai Qdrant)
│   └── processed_urls.txt           # Tracking URL yang sudah diproses
│
├── tests/
│   ├── test_scraper.py
│   ├── test_filter.py
│   └── test_retriever.py
│
├── scripts/
│   └── init_vector_db.py            # Setup awal Qdrant collection
│
├── Dockerfile                       # Untuk deployment dashboard
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Tech Stack & Justifikasi

### AI & ML

| Komponen | Library/Service | Alasan | Biaya |
|---|---|---|---|
| Orchestration | LangGraph | State machine yang jelas, lebih kontrol vs CrewAI | Gratis (OSS) |
| LLM (utama) | Gemini 2.0 Flash | 1.500 req/hari gratis, cepat, murah | Gratis |
| LLM (fallback) | Groq + Llama 3.1 | Kecepatan tinggi, gratis dengan rate limit | Gratis |
| Embedding | Gemini text-embedding-004 | 1.500 req/hari, 768 dimensi, akurat | Gratis |

### Database & Storage

| Komponen | Pilihan | Kapan dipakai | Biaya |
|---|---|---|---|
| Vector DB (prod) | Qdrant Cloud | Persistent, share antar run GitHub Actions | Gratis (1 GB) |
| Vector DB (dev) | FAISS | Development lokal, tidak perlu internet | Gratis (OSS) |
| Summary storage | JSON file di repo | Sederhana, tidak butuh DB | Gratis |
| Backup storage | Supabase free tier | Jika butuh relational data | Gratis (500 MB) |

### Infrastructure

| Komponen | Service | Biaya |
|---|---|---|
| Automation/Cron | GitHub Actions | Gratis (2.000 mnt/bln, public repo) |
| Dashboard hosting | Koyeb | Gratis (512 MB RAM, 1 vCPU) |
| Notifikasi | Telegram Bot API | Gratis tanpa batas |
| Source code | GitHub | Gratis |

### Python Libraries

```txt
# requirements.txt

# Scraping
httpx==0.27.0
feedparser==6.0.11
beautifulsoup4==4.12.3

# AI / LLM
langchain==0.3.0
langgraph==0.2.0
langchain-google-genai==2.0.0
langchain-groq==0.2.0
google-generativeai==0.8.0

# Vector DB
qdrant-client==1.11.0
faiss-cpu==1.8.0

# Dashboard
streamlit==1.39.0

# Utilities
python-dotenv==1.0.0
pydantic==2.9.0
pydantic-settings==2.5.0
schedule==1.2.0
loguru==0.7.2

# Notifikasi
python-telegram-bot==21.6

# Testing
pytest==8.3.0
pytest-asyncio==0.24.0
```

---

## 5. Pipeline Detail

### 5.1 Stage 1 — Data Ingestion (Scraping)

**File:** `agents/scraper.py`

**Sumber berita (RSS Feeds):**

```yaml
# config/sources.yaml
sources:
  - name: Kompas
    url: https://rss.kompas.com/nasional
    category_hint: nasional

  - name: Detik
    url: https://rss.detik.com/index.php/detikcom
    category_hint: umum

  - name: CNBC Indonesia
    url: https://www.cnbcindonesia.com/rss
    category_hint: ekonomi

  - name: Tempo
    url: https://rss.tempo.co/nasional
    category_hint: nasional

  - name: Republika
    url: https://rss.republika.co.id/rss/all
    category_hint: umum
```

**Output schema per artikel:**

```python
@dataclass
class RawArticle:
    url: str
    title: str
    content: str          # Full text body
    source: str           # Nama media
    published_at: datetime
    category_hint: str    # Dari config sumber
```

**Logika scraper:**
1. Baca semua sumber dari `sources.yaml`
2. Fetch RSS feed dengan `feedparser`
3. Untuk setiap entry: cek apakah URL sudah ada di `processed_urls.txt`
4. Jika baru: fetch full content dengan `httpx` + `BeautifulSoup`
5. Return list `RawArticle`

---

### 5.2 Stage 2 — Smart Filter Agent (Agentic)

**File:** `agents/filter.py`

**Tugas agent:**

1. **Deduplikasi** — Generate embedding sementara untuk tiap artikel baru, hitung cosine similarity dengan artikel yang sudah ada. Jika similarity > 0.92, buang artikel baru.

2. **Klasifikasi kategori** — Gunakan Gemini Flash dengan prompt zero-shot:

```python
CLASSIFY_PROMPT = """
Klasifikasikan artikel berita berikut ke dalam SATU kategori:
[Ekonomi, Politik, Teknologi, Kesehatan, Olahraga, Hiburan, Internasional, Lingkungan, Hukum, Umum]

Judul: {title}
Konten (300 karakter pertama): {content_preview}

Jawab HANYA dengan nama kategori, tanpa penjelasan.
"""
```

3. **Scoring relevansi** — Artikel dengan konten < 200 karakter atau tidak ada body langsung dibuang.

**Output:** List `FilteredArticle` yang sudah bersih dan terklasifikasi.

---

### 5.3 Stage 3 — Knowledge Base (RAG)

**File:** `agents/embedder.py` + `rag/vector_store.py`

**Flow embedding:**

```python
# Setiap artikel diubah menjadi "document string" sebelum di-embed
def prepare_document(article: FilteredArticle) -> str:
    return f"""
    Judul: {article.title}
    Kategori: {article.category}
    Sumber: {article.source}
    Tanggal: {article.published_at.strftime('%d %B %Y')}
    
    {article.content[:2000]}
    """
```

**Metadata yang disimpan di Qdrant:**

```python
payload = {
    "url": article.url,
    "title": article.title,
    "source": article.source,
    "category": article.category,
    "published_at": article.published_at.isoformat(),
    "summary": "",        # Diisi oleh summarizer
    "key_points": [],     # Diisi oleh summarizer
}
```

**Qdrant collection setup:**

```python
# scripts/init_vector_db.py
client.create_collection(
    collection_name="sekilas_ai",
    vectors_config=VectorParams(
        size=768,                    # Dimensi Gemini text-embedding-004
        distance=Distance.COSINE
    )
)
```

---

### 5.4 Stage 4 — Insight Generation (LangGraph)

**File:** `agents/summarizer.py` + `pipeline/orchestrator.py`

**LangGraph state:**

```python
class NewsState(TypedDict):
    articles: List[FilteredArticle]
    current_article: FilteredArticle
    summary: str
    key_points: List[str]
    category_digests: Dict[str, List[str]]
    daily_headline: str
    errors: List[str]
```

**Graph nodes:**

```
START
  │
  ▼
[summarize_article]     → Generate ringkasan 2-3 kalimat per artikel
  │
  ▼
[extract_key_points]    → Extract 3 poin penting
  │
  ▼
[update_vector_store]   → Update payload di Qdrant dengan summary
  │
  ▼
[build_category_digest] → Kelompokkan per kategori
  │
  ▼
[generate_headline]     → Buat 1 kalimat "berita terpenting hari ini"
  │
  ▼
[save_daily_digest]     → Simpan ke data/summaries.json
  │
  ▼
END
```

**Prompt summarization:**

```python
SUMMARIZE_PROMPT = """
Kamu adalah editor berita profesional. Ringkas artikel berikut dalam 2-3 kalimat dalam Bahasa Indonesia.
Fokus pada: siapa, apa, dampak.
Hindari: opini, kata-kata berlebihan, informasi tidak penting.

Judul: {title}
Konten: {content}

Ringkasan:
"""

KEY_POINTS_PROMPT = """
Dari artikel berikut, ekstrak tepat 3 poin penting dalam format bullet point singkat (maks 15 kata per poin).

Artikel: {content}

Format output (JSON):
{{"key_points": ["poin 1", "poin 2", "poin 3"]}}
"""
```

---

### 5.5 Stage 5 — Delivery

#### Telegram Notifikasi

**File:** `agents/notifier.py`

```python
DIGEST_TEMPLATE = """
🗞 *Sekilas.ai Daily Digest*
📅 {date}

🔥 *Headline Hari Ini*
{headline}

---

📊 *Ringkasan per Kategori*

{category_sections}

---
🤖 Powered by Sekilas.ai Agentic-RAG
🔗 Dashboard: {dashboard_url}
"""
```

#### Streamlit Dashboard

**File:** `dashboard/app.py`

**3 halaman utama:**

1. **Digest Harian** — Tampilkan ringkasan berita hari ini, dikelompokkan per kategori. Card per artikel dengan judul, sumber, ringkasan, dan key points.

2. **Cari Berita** — Input teks bebas → semantic search ke Qdrant → tampilkan top-5 hasil yang relevan dengan similarity score.

3. **Tanya AI** — Input pertanyaan → RAG chain → jawaban dengan kutipan sumber artikel.

---

## 6. Fase Pengerjaan

### Fase 1 — Core Pipeline (Minggu 1–2)

**Goal:** Pipeline berjalan end-to-end dari scraping sampai data tersimpan.

- [ ] Setup repo GitHub + struktur folder
- [ ] Buat `config/sources.yaml` dengan 5 sumber berita
- [ ] Implementasi `agents/scraper.py` (RSS + full content fetch)
- [ ] Setup Qdrant Cloud account + buat collection `sekilas_ai`
- [ ] Implementasi `agents/embedder.py` (Gemini embedding)
- [ ] Test pipeline manual: scrape → embed → simpan ke Qdrant
- [ ] Tambah `processed_urls.txt` untuk tracking duplikat URL

**Definisi Done Fase 1:** Menjalankan `python -m pipeline.orchestrator` secara manual berhasil menyimpan minimal 20 artikel ke Qdrant.

---

### Fase 2 — Agentic Intelligence (Minggu 3–4)

**Goal:** Filter agent dan summarization agent berjalan dengan LangGraph.

- [ ] Implementasi `agents/filter.py` (dedup via cosine similarity + klasifikasi)
- [ ] Setup LangGraph di `pipeline/orchestrator.py`
- [ ] Implementasi `agents/summarizer.py` (ringkasan + key points)
- [ ] Integrasi Groq sebagai fallback LLM (jika Gemini rate limit)
- [ ] Test klasifikasi dengan 50 artikel dari berbagai kategori
- [ ] Simpan hasil summary ke `data/summaries.json`

**Definisi Done Fase 2:** Deduplikasi berhasil menangkap artikel yang sama dari 2 sumber berbeda. Semua artikel ter-klasifikasi ke kategori yang tepat (validasi manual 20 artikel).

---

### Fase 3 — Automasi & Notifikasi (Minggu 5)

**Goal:** Pipeline berjalan otomatis setiap hari tanpa intervensi.

- [ ] Buat `.github/workflows/daily_pipeline.yml`
- [ ] Setup semua secrets di GitHub (API keys)
- [ ] Test GitHub Actions secara manual (`workflow_dispatch`)
- [ ] Setup Telegram Bot via @BotFather
- [ ] Implementasi `agents/notifier.py`
- [ ] Test kiriman digest ke Telegram

**Definisi Done Fase 3:** Pipeline berjalan otomatis di GitHub Actions dan digest terkirim ke Telegram setiap pagi.

---

### Fase 4 — Dashboard & Deployment (Minggu 6–7)

**Goal:** Dashboard publik yang bisa diakses siapa saja.

- [ ] Implementasi `dashboard/pages/01_Digest_Harian.py`
- [ ] Implementasi `dashboard/pages/02_Cari_Berita.py` (semantic search UI)
- [ ] Implementasi `rag/retriever.py` + `rag/qa_chain.py`
- [ ] Implementasi `dashboard/pages/03_Tanya_AI.py` (RAG Q&A)
- [ ] Buat `Dockerfile` untuk dashboard
- [ ] Deploy ke Koyeb (connect GitHub repo)
- [ ] Test end-to-end dari Telegram link ke dashboard

**Definisi Done Fase 4:** Dashboard live dan dapat diakses via URL publik. Pencarian semantik mengembalikan hasil relevan dalam < 3 detik.

---

### Fase 5 — Polish & Monitoring (Minggu 8)

**Goal:** Sistem stabil, ada logging, dan mudah di-maintain.

- [ ] Tambah `loguru` logging di semua agent
- [ ] Buat unit tests untuk `scraper`, `filter`, `retriever`
- [ ] Tambah error handling + retry logic di LangGraph nodes
- [ ] Monitoring sederhana: hitung artikel per hari, log ke `summaries.json`
- [ ] Dokumentasi `README.md` yang lengkap
- [ ] Buat `CONTRIBUTING.md` jika open source

---

## 7. Spesifikasi Setiap Komponen

### 7.1 Semantic Search (RAG Retriever)

```python
# rag/retriever.py

def search(query: str, top_k: int = 5, category_filter: str = None) -> List[SearchResult]:
    """
    1. Embed query menggunakan Gemini
    2. Query ke Qdrant dengan optional filter kategori
    3. Return top-k hasil dengan score similarity
    """
    
    # Optional: filter by category
    query_filter = None
    if category_filter:
        query_filter = Filter(
            must=[FieldCondition(
                key="category",
                match=MatchValue(value=category_filter)
            )]
        )
    
    results = client.search(
        collection_name="sekilas_ai",
        query_vector=embed(query),
        query_filter=query_filter,
        limit=top_k,
        with_payload=True
    )
    return results
```

### 7.2 RAG Q&A Chain

```python
# rag/qa_chain.py

QA_PROMPT = """
Kamu adalah asisten berita cerdas Sekilas.ai. 
Jawab pertanyaan pengguna HANYA berdasarkan konteks berita berikut.
Jika informasi tidak ada di konteks, katakan "Informasi ini belum ada di database berita saya."
Selalu sebutkan sumber berita yang kamu gunakan.

Konteks berita:
{context}

Pertanyaan: {question}

Jawaban (dalam Bahasa Indonesia):
"""

def answer(question: str) -> AnswerResult:
    # 1. Retrieve relevan articles
    articles = retriever.search(question, top_k=5)
    
    # 2. Build context string
    context = build_context(articles)
    
    # 3. Generate answer dengan Gemini
    response = gemini.generate(QA_PROMPT.format(
        context=context,
        question=question
    ))
    
    return AnswerResult(
        answer=response.text,
        sources=[a.payload["url"] for a in articles]
    )
```

### 7.3 Deduplication Logic

```python
# agents/filter.py

DEDUP_THRESHOLD = 0.92  # Tuning: lebih tinggi = lebih strict

def deduplicate(new_articles: List[RawArticle]) -> List[RawArticle]:
    unique = []
    seen_embeddings = []
    
    for article in new_articles:
        embedding = embed_text(article.title)  # Embed title saja (lebih cepat)
        
        # Cek similarity dengan semua artikel yang sudah lolos
        is_duplicate = False
        for seen_emb in seen_embeddings:
            similarity = cosine_similarity(embedding, seen_emb)
            if similarity > DEDUP_THRESHOLD:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(article)
            seen_embeddings.append(embedding)
    
    return unique
```

---

## 8. Konfigurasi GitHub Actions

```yaml
# .github/workflows/daily_pipeline.yml

name: Sekilas.ai Daily Pipeline

on:
  schedule:
    - cron: '0 0 * * *'      # Jam 00:00 UTC = 07:00 WIB
  workflow_dispatch:           # Manual trigger untuk testing

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 30        # Kill jika lebih dari 30 menit

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run scraping + filter + embed
        run: python -m pipeline.orchestrator
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

      - name: Commit updated data files
        run: |
          git config user.name "Sekilas.ai Bot"
          git config user.email "bot@sekilas.ai"
          git add data/summaries.json data/processed_urls.txt
          git diff --staged --quiet || git commit -m "🤖 Daily update: $(date +'%Y-%m-%d')"
          git push
```

### Secrets yang perlu di-set di GitHub

Masuk ke: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Cara Mendapatkan |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys |
| `QDRANT_URL` | Qdrant Cloud → Cluster → Dashboard (format: `https://xxx.qdrant.io`) |
| `QDRANT_API_KEY` | Qdrant Cloud → Cluster → API Keys |
| `TELEGRAM_BOT_TOKEN` | Chat dengan @BotFather di Telegram → `/newbot` |
| `TELEGRAM_CHAT_ID` | Chat dengan @userinfobot untuk mendapatkan ID kamu |

---

## 9. Free Tier Limits & Mitigasi

| Service | Batasan | Estimasi Usage | Mitigasi |
|---|---|---|---|
| **Gemini Flash** | 1.500 req/hari | ~100–200 artikel × 2 call = 200–400 req/hari | Aman. Jika melebihi, gunakan Groq |
| **Gemini Embedding** | 1.500 req/hari | ~100–200 artikel = 100–200 req/hari | Aman |
| **Groq (Llama)** | 6.000 token/menit | Burst saat summarize banyak artikel | Tambah `asyncio.sleep(1)` antar call |
| **GitHub Actions** | 2.000 menit/bulan | ~5–10 mnt/hari × 30 = 150–300 mnt/bulan | Aman. Sisa untuk testing manual |
| **Qdrant Cloud** | 1 GB storage | ~2KB/artikel × 10.000 artikel = ~20 MB | Aman untuk >1 tahun |
| **Koyeb** | 512 MB RAM | Streamlit idle ~100MB | Aman. Aktifkan hanya saat diakses |

### Strategi Penghematan API Call

```python
# Caching embedding untuk artikel yang sudah pernah diproses
# Jangan re-embed artikel yang sudah ada di Qdrant

# Batasi konten yang di-summarize (max 2000 karakter per artikel)
# Gunakan title-only embedding untuk dedup (lebih hemat vs full text)

# Batch embedding request jika memungkinkan
# Gemini mendukung batch hingga 100 teks sekaligus
```

---

## 10. Definisi Done (DoD)

### MVP (Minimum Viable Product)

Sistem dianggap MVP ketika:

- [x] Pipeline berjalan otomatis setiap hari tanpa error
- [x] Minimal 50 artikel unik masuk ke Qdrant per hari
- [x] Digest harian terkirim ke Telegram setiap pagi
- [x] Dashboard bisa diakses via URL publik
- [x] Pencarian semantik mengembalikan hasil dalam < 3 detik
- [x] Q&A menjawab pertanyaan berbasis artikel yang ada

### V1.0 (Production-Ready)

- [ ] Error handling lengkap di semua agent (tidak crash saat satu sumber gagal)
- [ ] Logging tersimpan dan bisa dimonitor
- [ ] Unit test coverage > 60%
- [ ] README.md dengan panduan setup lengkap
- [ ] Dashboard menampilkan statistik: artikel hari ini, kategori terbanyak, dll

### Backlog (Future Features)

- [ ] Personalisasi: user bisa set kategori favorit
- [ ] Multi-bahasa: support berita English (BBC, Reuters)
- [ ] Trend analysis: topik yang trending dalam 7 hari
- [ ] API endpoint: REST API untuk akses programatik
- [ ] Alert keyword: notifikasi jika kata kunci tertentu muncul di berita

---

*Last updated: Planning phase*  
*Maintained by: Sekilas.ai Team*
