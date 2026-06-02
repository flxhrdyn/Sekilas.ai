# Overhauled: High-Performance Agentic RAG, Rebalancing & CoT Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement model rebalancing, integrate English Chain-of-Thought (CoT) reasoning, realign the pipeline to run pre-filtering before downloading/clustering, implement Planner memory, optimize embedding vector payloads, build a Single-Pass Active QA Router, and transition persistence to JSONL.

**Architecture:** Model selection defaults are updated in settings. The pipeline flow is inverted: Scrape $\rightarrow$ Filter (Headline+Preview) $\rightarrow$ Fetch passed content $\rightarrow$ Cluster $\rightarrow$ Name. Planner reads the last 3 JSONL entries for historical memory. Summarizer bypasses synthesis for small clusters. Vector embeddings are pure chunk texts (summaries stored strictly in payload metadata). QA Chain executes a Single-Pass Router prompt, returning `[NEED_WEB_SEARCH]` for on-the-fly Tavily search fallback. Daily digest records are saved via append-only JSONL.

**Tech Stack:** Python, Groq SDK, LangGraph, Pydantic, Qdrant, Tavily API

---

### Task 1: Update Settings Configuration

**Files:**
- Modify: `backend/config/settings.py`

- [ ] **Step 1: Modify model settings and summaries_file path in settings.py**

Replace lines 30-33 in `backend/config/settings.py` with:
```python
    classifier_model: str = Field(default="llama-3.1-8b-instant", alias="CLASSIFIER_MODEL")
    summarizer_model: str = Field(default="llama-3.1-8b-instant", alias="SUMMARIZER_MODEL")
    qa_model: str = Field(default="llama-3.1-8b-instant", alias="QA_MODEL")
    planner_model: str = Field(default="qwen/qwen3-32b", alias="PLANNER_MODEL")
    researcher_model: str = Field(default="llama-3.1-8b-instant", alias="RESEARCHER_MODEL")
```

Modify line 54 to update default summaries file extension to `.jsonl`:
```python
    summaries_file: Path = Field(default=ROOT_DIR / "data" / "summaries.jsonl")
```

- [ ] **Step 2: Verify settings updates via python interactive check**

Run: `python -c "from backend.config.settings import get_settings; s = get_settings(); assert s.planner_model == 'qwen/qwen3-32b'; assert s.researcher_model == 'llama-3.1-8b-instant'; assert str(s.summaries_file).endswith('summaries.jsonl'); print('Settings verified!')"`
Expected: Prints `Settings verified!` and exits 0.

- [ ] **Step 3: Commit changes**

```bash
git add backend/config/settings.py
git commit -m "feat: configure settings model defaults and switch summaries file to JSONL"
```

---

### Task 2: NewsPlannerAgent Model, Prompt & Long-Term Memory Migration

**Files:**
- Modify: `backend/agents/planner.py`

- [ ] **Step 1: Update PLANNER_PROMPT to English with {historical_context} placeholder**

Replace `PLANNER_PROMPT` in `backend/agents/planner.py` with the English specification, removing any Indonesian words.

- [ ] **Step 2: Update NewsPlannerAgent constructor and signature**

Update constructor default `model` to `"qwen/qwen3-32b"` and update the signature and logging of `plan_research`:
```python
class NewsPlannerAgent:
    def __init__(self, api_key: str, model: str = "qwen/qwen3-32b") -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def plan_research(self, clusters_map: Dict[int, str], articles: Sequence[FilteredArticle], historical_context: str = "") -> List[Dict]:
```

Ensure the prompt formats `{historical_context}`:
```python
        prompt = PLANNER_PROMPT.format(
            clusters_data="\n".join(clusters_data),
            historical_context=historical_context or "No recent historical context available."
        )
```

- [ ] **Step 3: Test compilation of planner.py**

Run: `python -m py_compile backend/agents/planner.py`
Expected: Compiles with no syntax errors.

- [ ] **Step 4: Commit changes**

```bash
git add backend/agents/planner.py
git commit -m "feat: migrate planner to Qwen3-32B with Long-Term Memory support"
```

---

### Task 3: NewsResearcherAgent CoT & Language Migration

**Files:**
- Modify: `backend/agents/researcher.py`

- [ ] **Step 1: Rewrite RESEARCH_REFINER_PROMPT in English with CoT example**

Replace `RESEARCH_REFINER_PROMPT` in `backend/agents/researcher.py` with English instructions and a `<thinking>` few-shot.

- [ ] **Step 2: Update NewsResearcherAgent defaults and add thinking block stripping**

Modify the constructor `__init__`:
```python
    def __init__(self, tavily_api_key: str, groq_api_key: str, model: str = "llama-3.1-8b-instant") -> None:
```

Modify `_refine_results` to strip `<thinking>` tags from the final string:
```python
            ans = response.choices[0].message.content.strip()
            if "<think>" in ans or "<thinking>" in ans:
                import re
                ans = re.sub(r'<(thinking|think)>.*?</\1>', '', ans, flags=re.DOTALL).strip()
            return ans
```

Translate logs in `execute_research` to English.

- [ ] **Step 3: Test compilation of researcher.py**

Run: `python -m py_compile backend/agents/researcher.py`
Expected: Compiles successfully.

- [ ] **Step 4: Commit changes**

```bash
git add backend/agents/researcher.py
git commit -m "feat: update researcher agent to Llama 8B with English CoT"
```

---

### Task 4: NewsFilter (Classifier) Lightweight Pre-Filtering & Prompts Migration

**Files:**
- Modify: `backend/tools/filter.py`

- [ ] **Step 1: Update CATEGORIES to English labels**

Replace lines 16-27 in `backend/tools/filter.py` with:
```python
CATEGORIES: tuple[str, ...] = (
    "Economy",
    "Politics",
    "Technology",
    "Health",
    "Sports",
    "Entertainment",
    "International",
    "Environment",
    "Law",
    "General",
)
```

- [ ] **Step 2: Update BATCH_CLASSIFY_PROMPT to English with a CoT few-shot example**

Replace `BATCH_CLASSIFY_PROMPT` to operate efficiently on Headline + Preview fields in English, returning `classifications` in JSON format.

- [ ] **Step 3: Update `run` and `_classify_batch` to support lightweight pre-filtering**

Modify `run` signature to accept `Sequence[RawHeadline]` instead of `Sequence[RawArticle]`:
```python
    def run(self, headlines: Sequence[RawHeadline]) -> tuple[list[RawHeadline], FilterStats]:
```

Inside `run` and `_classify_batch`, perform deduplication and classification directly on the headlines and their RSS description previews (avoiding downloading full body text first). Discard spam dynamically before fetching HTML contents.

Modify `_heuristic_category` to support bilingual keywords.

- [ ] **Step 4: Test compilation of filter.py**

Run: `python -m py_compile backend/tools/filter.py`
Expected: Compiles successfully.

- [ ] **Step 5: Commit changes**

```bash
git add backend/tools/filter.py
git commit -m "feat: update classifier to support lightweight pre-filtering on RSS headlines"
```

---

### Task 5: NewsSummarizerAgent Prompts, CoT & Dynamic Synthesis Bypass

**Files:**
- Modify: `backend/agents/summarizer.py`

- [ ] **Step 1: Rewrite all 5 prompts in English with CoT thinking tags**

Translate all 5 prompt templates (`SUMMARIZE_AND_EXTRACT_PROMPT`, `HEADLINE_PROMPT`, `BATCH_NAMING_PROMPT`, `STORY_SYNTHESIS_PROMPT`, `CORRELATION_PROMPT`) to English, injecting 1 CoT few-shot to `SUMMARIZE_AND_EXTRACT_PROMPT` and `STORY_SYNTHESIS_PROMPT`.

- [ ] **Step 2: Add CoT thinking block cleanup to LLM calls**

Modify `_summarize_article` and `synthesize_story` to proactively strip `<thinking>` tags if returned.
Update constructor default:
```python
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama-3.1-8b-instant",
        max_content_chars: int = 2000,
    ) -> None:
```

- [ ] **Step 3: Implement dynamic synthesis bypass for small clusters**

Modify `synthesize_story` to directly bypass the LLM call if the cluster size is $\le 2$, returning a default structured dictionary using the representative article's key points, saving Groq API costs and latencies.

- [ ] **Step 4: Test compilation of summarizer.py**

Run: `python -m py_compile backend/agents/summarizer.py`
Expected: Compiles successfully.

- [ ] **Step 5: Commit changes**

```bash
git add backend/agents/summarizer.py
git commit -m "feat: migrate summarizer prompts to English and implement dynamic synthesis bypass"
```

---

### Task 6: NewsQAChain Single-Pass Router & Dynamic Web Fallback

**Files:**
- Modify: `backend/rag/qa_chain.py`

- [ ] **Step 1: Rewrite QA_PROMPT in English as a Single-Pass Router**

Update `QA_PROMPT` in `backend/rag/qa_chain.py` with English instructions and a `<thinking>` few-shot. Add the router instruction:
*"If the retrieved context does not contain sufficient specific information to answer the user's question, return ONLY the exact token: `[NEED_WEB_SEARCH]`."*

- [ ] **Step 2: Update NewsQAChain constructor to support Tavily API Key**

```python
class NewsQAChain:
    def __init__(
        self,
        retriever: NewsRetriever,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        default_top_k: int = 5,
        reranker: Any | None = None,
        tavily_api_key: str | None = None,
    ) -> None:
        self.retriever = retriever
        self.model_name = model.strip()
        self.default_top_k = default_top_k
        self.client = Groq(api_key=api_key)
        self.reranker = reranker
        from tavily import TavilyClient
        self.tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None
```

- [ ] **Step 3: Implement Single-Pass Evaluation & Dynamic Web Fallback**

Modify the `answer` method. Send a single QA call to Llama 8B. If the returned answer text contains the `[NEED_WEB_SEARCH]` token, trigger a dynamic Tavily search fallback, construct new context, and run a second QA call:
```python
        # RAG Search
        results = self.retriever.search(
            query=question,
            top_k=limit,
            category_filter=category_filter,
            reranker=self.reranker,
            days_limit=days_limit,
        )

        context = build_context(results) if results else "No context available."
        
        # First Pass
        answer_text = self._execute_qa_call(question, context)
        
        # Check for Router Fallback Token
        if "[NEED_WEB_SEARCH]" in answer_text and self.tavily_client:
            print(f"[RAG] Router triggered fallback search. Fetching web results for: {question}...")
            try:
                search_response = self.tavily_client.search(
                    query=question,
                    search_depth="advanced",
                    max_results=3
                )
                web_results = []
                for res in search_response.get("results", []):
                    from backend.rag.retriever import SearchResult
                    web_results.append(SearchResult(
                        title=res.get("title", "Web Result"),
                        content=res.get("content", ""),
                        url=res.get("url", ""),
                        source="Web Search",
                        published_at=None,
                        score=0.9
                    ))
                if web_results:
                    results = web_results + results
                    context = build_context(results)
                    # Second Pass
                    answer_text = self._execute_qa_call(question, context)
                    print(f"[RAG] Successfully resolved question with dynamic web context.")
            except Exception as e:
                print(f"[WARNING] Fallback search failed: {e}")
                answer_text = answer_text.replace("[NEED_WEB_SEARCH]", "The requested information was not found in our news database.")
```

Make sure the `_execute_qa_call` helper method handles `<thinking>` block stripping.

- [ ] **Step 4: Test compilation of qa_chain.py**

Run: `python -m py_compile backend/rag/qa_chain.py`
Expected: Compiles successfully.

- [ ] **Step 5: Commit changes**

```bash
git add backend/rag/qa_chain.py
git commit -m "feat: upgrade QA chain to a Single-Pass Active QA Router with Tavily fallback"
```

---

### Task 7: Orchestrator Pipeline Flow Realignment & JSONL Persistence

**Files:**
- Modify: `backend/pipeline/orchestrator.py`

- [ ] **Step 1: Realign pipeline node dependencies in `build_graph`**

Modify `build_graph` flow in `backend/pipeline/orchestrator.py`:
1. `scrape_node` runs.
2. `filter_node` runs classification *directly* on `raw_headlines` (RSSI previews).
3. The passed articles fetch their full HTML body:
```python
    def fetch_passed_content_node(state: NewsState) -> NewsState:
        passed_headlines = state.get("filtered_articles", []) # Headlines that passed filter
        raw_articles = scraper.fetch_full_contents(passed_headlines)
        # Convert RawArticle objects to FilteredArticle objects
        filtered_articles = []
        for art in raw_articles:
            # Match FilteredArticle schema
            # ...
        return {"filtered_articles": filtered_articles}
```
4. `cluster_node` runs clustering *only* on passed FilteredArticles.
5. `summarize_node` runs. Bypass `synthesize_story` if cluster size is $\le 2$.

- [ ] **Step 2: Optimize Chunk Embeddings Payload**

Modify `embed_node` so `text_to_embed = chunk_text` is pure and concise. The summary and key points are stored strictly in the payload dictionary metadata, not appended to the text being vectorized.

- [ ] **Step 3: Persist summaries via Append-Only JSONL**

Replace `_append_json_record` function in `backend/pipeline/orchestrator.py` to write JSONL to disk:
```python
def _append_json_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

Instantiate `NewsResearcherAgent` with `settings.researcher_model`. Ensure `tavily_api_key=settings.tavily_api_key` is passed to `NewsQAChain` in API routes.

- [ ] **Step 4: Test compilation of orchestrator.py**

Run: `python -m py_compile backend/pipeline/orchestrator.py`
Expected: Compiles with no syntax errors.

- [ ] **Step 5: Commit changes**

```bash
git add backend/pipeline/orchestrator.py
git commit -m "feat: realign pipeline nodes to optimize latency and implement append-only JSONL"
```

---

### Task 8: End-to-End Pipeline & Performance Verification

**Files:**
- Test: `scratch/test_performance.py`

- [ ] **Step 1: Create scratch performance test script**

Create `scratch/test_performance.py` to verify the aligned pre-filtering pipeline runs significantly faster and uses fewer API calls, and verify the Single-Pass Active QA Router triggers Tavily search *only* when the `[NEED_WEB_SEARCH]` token is returned.

- [ ] **Step 2: Run verification**

Run: `$env:PYTHONPATH="." ; python scratch/test_performance.py`
Expected: Successfully validates the pre-filtering speed, pure chunk vector payload sizes, and Single-Pass router logic.

- [ ] **Step 3: Clean up verification script**

Remove: `scratch/test_performance.py`

- [ ] **Step 4: Commit cleanup**

```bash
git rm scratch/test_performance.py
git commit -m "chore: remove performance verification scratch scripts"
```
