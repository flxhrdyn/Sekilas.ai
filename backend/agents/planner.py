from __future__ import annotations

import json
import time
from typing import Sequence, Dict, List
from groq import Groq
from backend.utils.llm_utils import extract_json
from backend.models.schemas import FilteredArticle
from backend.config.monitor import SystemMonitor

PLANNER_PROMPT = """
Kamu adalah Analis Strategis yang bertugas menentukan apakah sebuah topik berita memerlukan riset mendalam tambahan untuk memberikan wawasan intelijen yang lebih tajam.

TUGAS:
1. Tinjau daftar topik berita berikut.
2. Pilih maksimal 3 topik yang paling signifikan (Geopolitik, Ekonomi Makro, Kebijakan Publik, atau Disrupsi Teknologi).
3. Untuk setiap topik terpilih, buatlah 1-2 query pencarian spesifik untuk mendapatkan konteks historis, data terbaru, atau analisis pakar yang tidak ada di berita mentah.

Daftar Topik:
{clusters_data}

Kriteria Memilih Topik (Hanya pilih jika):
- Memiliki dampak luas pada masyarakat/ekonomi.
- Melibatkan kebijakan pemerintah yang kontroversial.
- Merupakan tren teknologi yang mengubah industri.
- Memerlukan data historis untuk memahami signifikansinya.

Kembalikan respon HANYA dalam format JSON:
{{
  "research_tasks": [
    {{
      "cluster_id": 0,
      "topic": "Judul Topik",
      "queries": ["query 1", "query 2"],
      "reason": "Alasan singkat kenapa butuh riset"
    }}
  ]
}}
""".strip()

class NewsPlannerAgent:
    def __init__(self, api_key: str, model: str = "llama-3-8b-8192") -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def plan_research(self, clusters_map: Dict[int, str], articles: Sequence[FilteredArticle]) -> List[Dict]:
        """
        Analyzes clusters and decides which ones need research.
        Returns a list of research tasks.
        """
        if not clusters_map:
            return []

        # Prepare cluster data for the prompt
        clusters_data = []
        for cid, name in clusters_map.items():
            # Get a few headlines from this cluster for context
            cluster_headlines = [a.title for a in articles if getattr(a, "cluster_id", -1) == cid][:3]
            clusters_data.append(f"ID: {cid} | Topik: {name} | Headlines: {'; '.join(cluster_headlines)}")

        prompt = PLANNER_PROMPT.format(clusters_data="\n".join(clusters_data))

        print(f"[PROCESS] Planner (Llama 8B) sedang menganalisis strategi riset untuk {len(clusters_map)} topik...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            SystemMonitor.increment_llm_usage()
            
            raw_text = response.choices[0].message.content
            result = extract_json(raw_text)
            
            tasks = result.get("research_tasks", [])
            
            if tasks:
                print(f"  [OK] Planner merekomendasikan riset untuk {len(tasks)} topik.")
                for t in tasks:
                    print(f"    - {t.get('topic')}: {t.get('reason')}")
            else:
                print("  [INFO] Planner memutuskan tidak ada topik yang memerlukan riset tambahan hari ini.")
                
            return tasks

        except Exception as e:
            print(f"  [!] Kesalahan Planner: {e}")
            return []
