# Sekilas.ai Agentic-RAG (Stage 1)

Implementasi Stage 1+2: scrape RSS berita, dedup + klasifikasi agentic, ringkas artikel + key points, generate embedding Gemini, lalu upsert ke Qdrant Cloud.

Orchestrator pipeline menggunakan LangGraph state machine dengan jalur kondisi:
- no-new-articles
- all-filtered-out
- success (upsert + persist digest)

## Setup cepat

1. Buat virtual environment Python 3.11+
2. Install dependency:
   pip install -r requirements.txt
3. Salin `.env.example` menjadi `.env`, lalu isi kredensial.
4. Inisialisasi collection Qdrant:
   python -m scripts.init_vector_db
5. Jalankan pipeline:
   python -m pipeline.orchestrator

## Catatan Dimensi Embedding

- Jika ingin dimensi 768, set EMBEDDING_OUTPUT_DIM=768.
- Jika model tidak mendukung pengaturan dimensi output, biarkan EMBEDDING_OUTPUT_DIM kosong.

## Stage 2 Agentic Filter

- Deduplikasi berbasis cosine similarity embedding dengan DEDUP_THRESHOLD.
- Filter kualitas konten minimum dengan MIN_CONTENT_CHARS.
- Klasifikasi kategori dengan CLASSIFIER_MODEL (fallback heuristik jika API gagal).

## Stage 2 Summarization

- Ringkasan 2-3 kalimat dan 3 key points per artikel dengan SUMMARIZER_MODEL.
- Panjang konten untuk ringkasan dibatasi SUMMARY_MAX_CONTENT_CHARS.
- Metadata summary dan key points disimpan ke payload Qdrant dan data/summaries.json.

## Stage 3 Automation And Notification

- Workflow harian tersedia di .github/workflows/daily_pipeline.yml.
- Pipeline dapat mengirim digest ke Telegram jika ENABLE_TELEGRAM_NOTIFY=true.
- Notifikasi dikirim setelah ingest sukses dan status notifikasi muncul di output pipeline.

## Prioritas Konfigurasi

- Aplikasi membaca nilai dari `.env`.
- Environment variable sistem/terminal tetap bisa dipakai dan akan override nilai `.env`.

## Output Stage 1

- Artikel baru disimpan ke Qdrant collection `sekilas_ai`
- URL terproses disimpan di `data/processed_urls.txt`
- Digest harian (headline + ringkasan per kategori + statistik pipeline) disimpan di `data/summaries.json`
- Jika notifier aktif, digest ringkas juga terkirim ke Telegram.
