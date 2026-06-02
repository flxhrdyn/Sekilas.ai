# Agent Model Rebalancing + CoT Design

**Date:** 2026-06-02  
**Branch:** feature/ui-ux-refinement-v3  
**Status:** Approved

## Overview

Reassign LLM models across all agents to optimize both quality and cost.
The Planner agent — which requires the highest-quality strategic reasoning to select which topics deserve deep research — is promoted to Qwen3-32B.
All other internal agents are migrated to Llama 3.1 8B with Chain-of-Thought (CoT) prompting to compensate for the smaller model's weaker reasoning.
All prompts and outputs are in **English** — both for better model performance and because the app UI is also migrating to English.

---

## Goals

1. **Quality**: Planner makes better strategic decisions with Qwen3-32B's deeper reasoning.
2. **Cost efficiency**: Llama 8B is significantly cheaper for high-volume tasks (summarize, classify, research refine).
3. **Language consistency**: Prompts and outputs fully in English across all agents. App UI will follow.

---

## Model Assignment

| Agent | File | Before | After |
|---|---|---|---|
| `NewsPlannerAgent` | `agents/planner.py` | `llama3-8b-8192` | `qwen/qwen3-32b` |
| `NewsResearcherAgent` | `agents/researcher.py` | `llama3-8b-8192` | `llama-3.1-8b-instant` + CoT |
| `NewsSummarizerAgent` | `agents/summarizer.py` | `qwen/qwen3-32b` | `llama-3.1-8b-instant` + CoT |
| NewsFilter (classifier) | `tools/filter.py` | `qwen/qwen3-32b` | `llama-3.1-8b-instant` + CoT |
| QA Chain | `rag/qa_chain.py` | `qwen/qwen3-32b` | `llama-3.1-8b-instant` + CoT |

**Groq model string:** `llama-3.1-8b-instant` (128K context, fastest Llama 8B on Groq)

---

## Settings Changes (`config/settings.py`)

Add a new `researcher_model` field. Rename `planner_model` semantics:

```python
planner_model: str = Field(default="qwen/qwen3-32b", alias="PLANNER_MODEL")
researcher_model: str = Field(default="llama-3.1-8b-instant", alias="RESEARCHER_MODEL")
summarizer_model: str = Field(default="llama-3.1-8b-instant", alias="SUMMARIZER_MODEL")
classifier_model: str = Field(default="llama-3.1-8b-instant", alias="CLASSIFIER_MODEL")
qa_model: str = Field(default="llama-3.1-8b-instant", alias="QA_MODEL")
```

---

## Chain-of-Thought (CoT) Implementation

**Approach:** 1 few-shot example with `<thinking>` wrapper in each agent's prompt.

The `<thinking>` block is part of the assistant's example response — it trains the model to reason before outputting the final answer. This is not an API feature; it's prompt engineering.

**Template pattern:**
```
[System prompt in English, instructing task]

Example:
User: [example input]
Assistant: <thinking>
[Reasoning steps — what to consider, how to approach it]
</thinking>
[Final answer in English]
```

The `<thinking>` block is stripped from the actual output before use — it only exists in the few-shot example to guide the model's reasoning style.

---

## Language Behavior

**All layers — English in, English out.**

| Layer | Prompt Language | Output Language |
|---|---|---|
| All internal agents (Planner, Researcher, Summarizer, Classifier) | English | English |
| QA Chain | English | English |

> **Note:** App UI migration to English is a separate task outside this spec's scope.

---

## Files to Modify

### `backend/config/settings.py`
- Add `researcher_model` field (`RESEARCHER_MODEL` env var)
- Update defaults: `planner_model` → `qwen/qwen3-32b`, `summarizer_model` / `classifier_model` / `qa_model` → `llama-3.1-8b-instant`

### `backend/agents/planner.py`
- Rewrite `PLANNER_PROMPT` in English
- Output instruction: respond in English
- Remove CoT (Qwen3-32B has strong built-in reasoning; CoT adds unnecessary tokens)
- Update log message: `"[PROCESS] Planner (Qwen3-32B) analyzing research strategy..."`

### `backend/agents/researcher.py`
- Rewrite `RESEARCH_REFINER_PROMPT` in English
- Add 1 CoT few-shot example with `<thinking>` tag
- Output instruction: English
- Accept `model` param from settings (`researcher_model`)

### `backend/agents/summarizer.py`
- Rewrite all prompts in English (summarize, synthesize, headline, correlations, topic naming)
- Add CoT few-shot to `summarize_article` and `synthesize_story` methods (highest cognitive load)
- Output instruction: English for all methods
- Update `model_name` default to `llama-3.1-8b-instant`

### `backend/tools/filter.py`
- Rewrite classifier prompt in English
- Add CoT few-shot: 1 example showing category reasoning before final label
- Output: category label in English
- Update `classifier_model` default

### `backend/rag/qa_chain.py`
- Rewrite system prompt in English
- Output instruction: respond in English
- Add CoT few-shot: 1 example showing reasoning through retrieved context before answering
- Remove existing multilingual language-detection instruction (no longer needed)

### `backend/pipeline/orchestrator.py`
- Update log message for Planner node: `"Planner (Qwen3-32B)"`
- Pass `researcher_model` from settings to `NewsResearcherAgent`

---

## Verification Plan

1. Run pipeline once after implementation
2. Observe Planner output: does it select more strategically relevant topics vs before?
3. Check Summarizer output quality in digest: comparable to Qwen3-32B?
4. Test QA Chain: verify answers are in English regardless of query language
5. Check LLM usage counter — should be lower cost (fewer Qwen3-32B calls)

---

## Open Questions (Resolved)

- ~~Which CoT approach for Llama 8B?~~ → 1 few-shot + `<thinking>` wrapper
- ~~How many examples?~~ → 1 per agent (token-efficient)
- ~~All agent output language?~~ → English (app UI also migrating to English)
- ~~QA output language?~~ → English (fixed, not language-adaptive)
