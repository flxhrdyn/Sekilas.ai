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
graph TB
    subgraph UI_Layer [1. User Experience Layer]
        UI[React Glassmorphism Dashboard] <--> API[FastAPI Gateway]
    end

    subgraph Orchestration_Layer [2. Agentic Orchestration Layer]
        API <--> QA_Agent[QA Intelligence Agent]
        QA_Agent --> Reranker[Llama 3.1 8B Reranker]
        
        Pipeline[Ingestion Pipeline] --> Planner[Strategic Planner]
        Planner --> Researcher[Deep Researcher]
        Researcher --> Summarizer[Intelligence Summarizer]
    end

    subgraph Knowledge_Layer [3. Knowledge & Memory Layer]
        Summarizer --> Embedder[FastEmbed Engine]
        Embedder --> QDR[(Qdrant Vector DB)]
        QDR <--> QA_Agent
    end

    subgraph External_Layer [4. External Integration Layer]
        Researcher <--> Tavily[Tavily Search API]
        Scraper[News Scraper] --> RSS[RSS Feeds]
        Scraper --> Pipeline
    end

    %% Styling
    style UI_Layer fill:#f0f7ff,stroke:#007acc,stroke-width:2px
    style Orchestration_Layer fill:#fff5f5,stroke:#ff4b4b,stroke-width:2px
    style Knowledge_Layer fill:#f0fff4,stroke:#38a169,stroke-width:2px
    style External_Layer fill:#fffaf0,stroke:#d69e2e,stroke-width:2px
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
