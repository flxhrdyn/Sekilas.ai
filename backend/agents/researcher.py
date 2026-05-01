from __future__ import annotations

import time
from typing import List, Dict
from tavily import TavilyClient
from groq import Groq
from backend.config.monitor import SystemMonitor

RESEARCH_REFINER_PROMPT = """
Kamu adalah Peneliti Intelijen yang bertugas menyaring informasi mentah dari hasil pencarian web.

TUGAS:
1. Tinjau hasil pencarian mentah untuk topik: "{topic}"
2. Ekstrak hanya fakta, data, atau konteks baru yang paling relevan dan kredibel.
3. Buang informasi yang berulang, iklan, atau tidak relevan.
4. Ringkas temuan dalam 3-4 poin fakta yang padat.

Hasil Pencarian Mentah:
{raw_results}

Kembalikan jawaban dalam Bahasa Indonesia yang profesional dan padat (tanpa basa-basi).
""".strip()

class NewsResearcherAgent:
    def __init__(self, tavily_api_key: str, groq_api_key: str, model: str = "llama-3-8b-8192") -> None:
        self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = model

    def execute_research(self, tasks: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Executes research queries using Tavily AND refines them using LLM (Llama 8B).
        This makes it a true Agentic Researcher.
        """
        if not tasks:
            return {}

        results_map: Dict[int, List[Dict]] = {}
        
        print(f"[PROCESS] Researcher Agent sedang menginvestigasi {len(tasks)} topik...")

        for task in tasks:
            cluster_id = task.get("cluster_id")
            queries = task.get("queries", [])
            topic = task.get("topic", "Unknown")
            
            if cluster_id is None or not queries:
                continue
                
            print(f"  [>] Searching: {topic}...")
            
            raw_data_chunks = []
            for query in queries:
                # Cleaning ultra-agresif:
                # 1. Ganti tanda hubung dengan spasi (penting untuk nama seperti Thompson-Herah)
                # 2. Hapus karakter non-alfanumerik sisa (kecuali spasi)
                import re
                clean_query = query.replace("-", " ")
                clean_query = re.sub(r'[^\w\s]', '', clean_query)
                clean_query = " ".join(clean_query.split()).strip()
                
                if not clean_query: continue
                
                try:
                    # Mencoba Advanced Search dulu
                    response = self.tavily_client.search(
                        query=clean_query,
                        search_depth="advanced",
                        max_results=3
                    )
                except Exception as e:
                    # Cetak error lebih detail untuk debugging
                    error_msg = str(e)
                    print(f"    [!] Advanced search gagal: {error_msg}")
                    
                    # FALLBACK: Coba Basic
                    try:
                        response = self.tavily_client.search(
                            query=clean_query,
                            search_depth="basic",
                            max_results=3
                        )
                    except Exception as e2:
                        # FALLBACK KEDUA: Simplifikasi query (ambil kata kunci saja)
                        print(f"    [!] Basic search pun gagal, mencoba simplifikasi query...")
                        simple_query = " ".join([w for w in clean_query.split() if len(w) > 3][:6])
                        try:
                            response = self.tavily_client.search(
                                query=simple_query,
                                search_depth="basic",
                                max_results=3
                            )
                        except Exception as e3:
                            print(f"    [!] Gagal total mencari '{clean_query}': {e3}")
                            continue
                
                time.sleep(1.0) # Jeda sopan antar query
                
                for res in response.get("results", []):
                    raw_data_chunks.append(f"Source: {res.get('url')}\nContent: {res.get('content')[:800]}")
            
            if not raw_data_chunks:
                continue

            # --- THE AGENTIC REFINING STEP ---
            print(f"  [PROCESS] Researcher Agent (Llama 8B) sedang memvalidasi dan menyaring temuan...")
            refined_facts = self._refine_results(topic, "\n---\n".join(raw_data_chunks))
            
            if refined_facts:
                # We store it in a way the summarizer can easily consume
                results_map[cluster_id] = [{
                    "title": f"Deep Research: {topic}",
                    "content": refined_facts
                }]
                print(f"    [OK] Investigasi selesai. Fakta kunci berhasil diekstraksi.")

        return results_map

    def _refine_results(self, topic: str, raw_results: str) -> str:
        """Uses LLM to turn messy search results into clean intelligence points."""
        prompt = RESEARCH_REFINER_PROMPT.format(topic=topic, raw_results=raw_results)
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            SystemMonitor.increment_llm_usage()
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"    [!] Gagal menyaring hasil riset: {e}")
            return raw_results[:2000] # Fallback to raw if LLM fails
