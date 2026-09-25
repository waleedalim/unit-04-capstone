# Multi-Agent RAG System for Enterprise Documentation

A Python CLI system that answers enterprise questions by routing them to
specialized agents: a semantic-search agent over documentation, a
natural-language-to-SQL agent over structured data, or both.

Status: **Silver tier** -- all three agents implemented and integrated
(Manager, Qualitative RAG, Quantitative NL-to-SQL), with unit tests for each.

## Architecture

```
                        ┌────────────────────┐
   user query  ──────▶  │   Manager Agent     │
                        │  (classify + route) │
                        └──────────┬──────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
        qualitative only   quantitative only      complex (both)
                 │                 │                 │
                 ▼                 ▼                 ▼
       ┌──────────────────┐ ┌──────────────────┐     merge + label
       │ Qualitative Agent│ │Quantitative Agent│     each agent's
       │  embed → Chroma  │ │  NL → SQL →      │     contribution
       │  semantic search │ │  SQLite → summary│
       │  + LLM synthesis │ │                  │
       │  + citations     │ │                  │
       └──────────────────┘ └──────────────────┘
```

- **Manager Agent** (`src/agents/manager_agent.py`): keyword-based
  classifier that labels a query `qualitative`, `quantitative`, `complex`
  (needs both), or `unclear` (asks the user to clarify). For `complex`
  queries it calls both agents and returns one response with each
  agent's contribution clearly labeled.
- **Qualitative Agent** (`src/agents/qualitative_agent.py`): chunks the
  sample docs in `src/data/docs/`, embeds them with
  `sentence-transformers` (local, no API key needed), stores them in a
  persistent Chroma collection, retrieves the top-k chunks above a
  similarity threshold, and asks an LLM to answer using only that
  context. Every answer carries citations (source file, chunk id,
  similarity score).
- **Quantitative Agent** (`src/agents/quantitative_agent.py`): translates
  a question into a SQLite `SELECT` statement (via an LLM when one is
  configured, or a small rule-based fallback otherwise), executes it
  against the sample `sales`/`customers` tables, and summarizes the
  result. Only `SELECT` statements are allowed to run.
- **LLM abstraction** (`src/llm_client.py`): agents depend on an
  `LLMClient` interface, not a specific vendor. `AnthropicLLMClient` is
  used when `ANTHROPIC_API_KEY` is set (preferred), `OpenAILLMClient` when
  only `OPENAI_API_KEY` is set, and otherwise a dependency-free
  `FallbackLLMClient` keeps the whole pipeline runnable (and testable)
  offline.

## Setup

Requires Python 3.11 or 3.12 -- the vector-DB/embedding stack (chromadb,
sentence-transformers/torch) does not yet ship prebuilt wheels for very
new Python versions (e.g. 3.13/3.14), which causes source builds to fail.

```bash
python3.12 -m venv .venv      # or python3.11
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on Linux/macOS
pip install -r requirements.txt
cp .env.example .env          # optional: add ANTHROPIC_API_KEY (or OPENAI_API_KEY) for real LLM answers
python -m src.db.init_db      # seed the sample SQLite database
```

The first run also downloads the `sentence-transformers` embedding model
(`all-MiniLM-L6-v2`), which requires internet access once; it's cached
locally after that.

## Usage

Interactive REPL:

```bash
python -m src.cli
```

One-shot query:

```bash
python -m src.cli -q "What is our company's security policy?"
python -m src.cli -q "Show me monthly revenue trends"
python -m src.cli -q "Compare Q4 performance across regions and explain our code review process"
```

Without an API key, qualitative answers fall back to raw retrieved
context (no generated synthesis) and quantitative queries only work for a
handful of rule-based phrasings (`monthly revenue`, `churn rate`,
`compare regions`, `Q1`-`Q4` + `region`, `total revenue`). Set
`ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) in `.env` for full NL-to-SQL
translation and generated answers.

## Sample data

- `src/data/docs/`: three markdown "policy" documents (security, code
  review, customer complaints) used by the qualitative agent.
- `src/db/init_db.py`: seeds a SQLite `enterprise.db` with a year of
  synthetic `sales` (by region/quarter) and `customers` (with churn
  dates) rows for the quantitative agent.

## Tests

```bash
pytest
```

Covers each agent in isolation (routing/classification logic, retrieval
+ citation thresholding, NL-to-SQL translation and execution guardrails)
plus manager-level integration tests for qualitative-only,
quantitative-only, complex (multi-agent), and unclear/clarification
query paths. Tests use `FallbackLLMClient` so they run without network
access or an API key.

## Project layout

```
src/
  agents/
    manager_agent.py
    qualitative_agent.py
    quantitative_agent.py
  data/docs/            sample enterprise documents
  db/
    schema.sql
    init_db.py
  cli.py
  config.py
  llm_client.py
tests/
  test_manager_agent.py
  test_qualitative_agent.py
  test_quantitative_agent.py
  test_cli.py
```

## Known limitations / next steps toward Gold

- No FastAPI layer, structured logging, or `/health` endpoint yet.
- Manager classification is keyword-based, not LLM-based -- works well
  for the documented query types but is not a general classifier.
- No automated relevance-threshold evaluation harness (retrieval quality
  is checked manually via `tests/test_qualitative_agent.py`).
