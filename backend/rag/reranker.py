from __future__ import annotations
import json
import logging
from typing import List
from groq import Groq
from backend.rag.retriever import SearchResult
from backend.config.monitor import SystemMonitor

logger = logging.getLogger(__name__)

RERANK_PROMPT = """
Tugas: Urutkan ulang (Rerank) hasil pencarian berikut berdasarkan RELEVANSI terhadap kueri pengguna.

Kueri Pengguna: "{query}"

Daftar Kandidat:
{documents}

INSTRUKSI:
1. Urutkan berdasarkan seberapa akurat dokumen menjawab kueri.
2. Prioritaskan berita yang fokus utamanya sesuai dengan subjek kueri.
3. Kembalikan HANYA daftar ID dalam format JSON array, contoh: [2, 0, 1, 3]
4. Jangan memberikan penjelasan apapun, hanya JSON array.
""".strip()

class NewsReranker:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        if not results or len(results) <= 1:
            return results

        # Persiapkan data untuk LLM (Top 25 saja untuk efisiensi dan akurasi)
        candidates = []
        for i, r in enumerate(results[:25]):
            candidates.append(f"[{i}] Judul: {r.title} | Cuplikan: {r.text_chunk[:200]}...")
        
        docs_text = "\n".join(candidates)
        
        try:
            print(f"[PROCESS] Reranker (Llama 8B) sedang mengurutkan ulang {len(results[:15])} hasil...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": RERANK_PROMPT.format(query=query, documents=docs_text)}],
                temperature=0,
                response_format={"type": "json_object"} if "llama-3.1" in self.model else None
            )
            
            content = response.choices[0].message.content
            # Extract list of IDs. Since we asked for JSON array, but used json_object mode, 
            # we might need to handle the structure.
            # Let's try to be robust.
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "ids" in data:
                    new_order = data["ids"]
                elif isinstance(data, list):
                    new_order = data
                else:
                    # Fallback for json_object mode which might force a key
                    new_order = list(data.values())[0] if isinstance(data, dict) else []
            except:
                import re
                match = re.search(r'\[[\d,\s]+\]', content)
                new_order = json.loads(match.group(0)) if match else []

            SystemMonitor.increment_llm_usage()

            # Map back to SearchResult objects
            reranked: List[SearchResult] = []
            seen_indices = set()
            
            for idx in new_order:
                if isinstance(idx, int) and 0 <= idx < len(results) and idx not in seen_indices:
                    reranked.append(results[idx])
                    seen_indices.add(idx)
            
            # Add remaining results that were not in the new_order (if any)
            for i, r in enumerate(results):
                if i not in seen_indices:
                    reranked.append(r)
            
            print("[OK] Reranking selesai.")
            return reranked

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            print(f"[!] Reranking gagal: {e}. Menggunakan urutan asli.")
            return results
