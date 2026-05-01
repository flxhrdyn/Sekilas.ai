<div align="center">

  # Sekilas.ai — Intelligent Multi-Agent News Intelligence
  **Autonomous Multi-Agent Orchestration, Deep Research, and Agentic-RAG with Reasoning.**
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
  [![Groq](https://img.shields.io/badge/Groq_LPU-F55036?style=for-the-badge&logo=rocket&logoColor=white)](https://groq.com/)
  [![Qdrant](https://img.shields.io/badge/Qdrant-FF4B4B?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
  [![Tavily](https://img.shields.io/badge/Tavily_Search-4285F4?style=for-the-badge&logo=google-search&logoColor=white)](https://tavily.com/)
  [![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
</div>

---

## Overview

**Sekilas.ai** is a state-of-the-art **Multi-Agent System (MAS)** designed to automate the entire news intelligence lifecycle. Unlike traditional aggregators, Sekilas.ai employs specialized AI agents to plan research, investigate external sources, and synthesize complex storylines into actionable intelligence.

This project demonstrates a high-performance **Agentic-RAG** implementation that combines semantic retrieval with cross-model reranking to deliver factual, grounded, and context-aware responses.

## Multi-Agent Architecture

The system is powered by a collaborative agentic workflow:

- **Strategic Planner (Llama 3.1 8B)**: Analyzes trending headlines and identifies topics requiring deep investigation.
- **Deep Researcher (Tavily + Llama 8B)**: Executes autonomous web research to gather historical context and external facts.
- **Intelligence Summarizer (Qwen 2.5 32B)**: Synthesizes raw data and research findings into structured "Story Syntheses" and "Strategic Correlations."
- **Agentic-RAG (Hybrid Search + Reranker)**: An advanced QA agent that utilizes **RRF (Reciprocal Rank Fusion)** and **Llama-based Reranking** to ensure the highest factual precision.

## Key Technical Features

- **Hybrid Intelligence Stack**: Leveraging **Groq Cloud** for ultra-fast inference using **Qwen 2.5 32B** (Summarization) and **Llama 3.1 8B** (Planning & Reranking).
- **Deep Research Integration**: Real-time investigation of niche topics using **Tavily AI** to prevent hallucinations and bridge information gaps.
- **Advanced RAG Pipeline**: High-precision retrieval using **Qdrant** with **Hybrid Search** (Dense + Sparse/BM25) and a dedicated **Cross-Encoder Reranking** stage.
- **Dynamic Reasoning UI**: A transparent "Reasoning Process" logger in the QA interface that shows the agent's internal logic steps in real-time.
- **Temporal Grounding**: Strict awareness of current dates and times to ensure news-at-hand accuracy (WIB Timezone support).

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Orchestration**: Custom State-Based Multi-Agent Logic
- **AI Models**: Qwen 2.5 32B, Llama 3.1 8B, all-MiniLM-L6-v2 (Local Embedding)
- **Search**: Tavily Search API
- **Scraping**: BeautifulSoup4, Feedparser

### Frontend
- **Framework**: React 18+ (TypeScript)
- **Styling**: Vanilla CSS (Premium Glassmorphism Design)
- **Animations**: CSS3 Transitions & Motion-driven logic
- **Icons**: Lucide React

### Infrastructure
- **Vector DB**: Qdrant (Cloud/Local)
- **Deployment**: Docker, GitHub Actions (Daily Cron Pipeline)

## System Flow

```mermaid
graph TD
    subgraph Pipeline [Autonomous Intelligence Pipeline]
        RSS[RSS Feeds] --> Scrape[News Scraper]
        Scrape --> Cluster[News Clustering]
        Cluster --> Filter[Agentic Quality Filter]
        Filter --> Planner[Strategic Planner]
        Planner -->|Research Tasks| Research[Deep Researcher]
        Research -->|Fact Injection| Summarizer[Intelligence Summarizer]
        Summarizer -->|Insights| Embed[Local Embedding Engine]
        Embed -->|Vector Upsert| QDR[(Qdrant Vector DB)]
    end
    
    subgraph Application [Agentic RAG Gateway]
        User[User Query] --> API[FastAPI Gateway]
        API -->|Hybrid Search| QDR
        QDR -->|Top 40 Chunks| Rerank[Llama 8B Reranker]
        Rerank -->|Top 5 Context| Qwen[Qwen 32B QA Agent]
        Qwen -->|Grounded Answer| User
    end

    style QDR fill:#f96,stroke:#333,stroke-width:4px
```

---

## Configuration

Required Environment Variables:
- `GROQ_API_KEY`: For Llama & Qwen models.
- `TAVILY_API_KEY`: For the Deep Researcher agent.
- `QDRANT_URL` / `QDRANT_API_KEY`: Vector database credentials.
- `EMBEDDING_MODEL`: Current: `sentence-transformers/all-MiniLM-L6-v2`.

---

## Author

**Felix Hardyan**
*   [GitHub](https://github.com/flxhrdyn)
