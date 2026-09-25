# Unit-04-Capstone

A Python CLI that answers enterprise questions by routing them to the right agent: semantic search over documents, NL-to-SQL over structured data, or both. All three agents (Manager, Qualitative RAG, Quantitative NL-to-SQL) implemented, integrated, and unit tested.

- **Manager** ([src/agents/manager_agent.py](src/agents/manager_agent.py)): classifies each query and routes it; for `complex` queries it calls both agents and labels each contribution.
- **Qualitative Agent** ([src/agents/qualitative_agent.py](src/agents/qualitative_agent.py)): embeds `src/data/docs/*.md` with `sentence-transformers`, retrieves top-k chunks above a similarity threshold from Chroma, and asks an LLM to answer using only that context. Every answer carries citations (source, chunk id, similarity score).
- **Quantitative Agent** ([src/agents/quantitative_agent.py](src/agents/quantitative_agent.py)): translates a question into a SQLite `SELECT` (via LLM, or a rule-based fallback), executes it against sample `sales`/`customers` tables, and summarizes the result.
- **LLM abstraction** ([src/llm_client.py](src/llm_client.py)): agents depend on an `LLMClient` interface, not a vendor. Uses Anthropic (Claude) if `ANTHROPIC_API_KEY` is set, OpenAI if only `OPENAI_API_KEY` is set, otherwise a dependency-free fallback so the whole pipeline still runs (and is fully unit-testable) with no key at all.

## How to run the project

No API key needed.. the full test suite runs against a fallback LLM stub, so all agent/routing/retrieval logic is verifiable with zero setup cost:

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Python 3.11/3.12 required
pip install -r requirements.txt
python -m src.db.init_db
pytest -v
```

To see real generated answers (what's shown in the demo below), add your own Anthropic API key:

```bash
cp .env.example .env   # then edit .env, set ANTHROPIC_API_KEY=sk-ant-...
python -m src.cli -q "What is our company's security policy?"
```

I tested this project end-to-end with my own Anthropic (Claude Haiku 4.5) API key -> see [Demo](#demo) below for real captured output. I'm not sharing this key publicly (it's a personal credential with billing attached); the fallback mode above demonstrates full functionality without one.

## Demo

Qualitative query (semantic search + cited answer):

```
$ python -m src.cli -q "What is our company's security policy?"

[QUALITATIVE] What is our company's security policy?
------------------------------------------------------------
Based on our documentation (security_policy.md), our company security policy includes:

## Access Control
All employees must use multi-factor authentication (MFA) for access to
company systems... Access to production systems is granted on a
least-privilege basis and reviewed quarterly by the Security team.

## Incident Response
Any suspected security incident must be reported to security@company.com
within one hour of discovery, following a four-phase runbook:
containment, eradication, recovery, post-incident review.

Sources:
  - security_policy.md (security_policy::0), similarity=0.7898
  - security_policy.md (security_policy::1), similarity=0.5098
  - security_policy.md (security_policy::3), similarity=0.4485
```

Quantitative query (NL-to-SQL + execution + insight):

```
$ python -m src.cli -q "Show me monthly revenue trends"

[QUANTITATIVE] Show me monthly revenue trends
------------------------------------------------------------
Revenue remained relatively stable throughout 2024, fluctuating between
approximately $119K and $128K per month. The strongest performance
occurred in September and October, while January was the weakest month.

SQL: SELECT strftime('%Y-%m', sale_date) as month, SUM(revenue) as total_revenue FROM sales GROUP BY strftime('%Y-%m', sale_date) ORDER BY month;
month      total_revenue
-------  ---------------
2024-01           119422
2024-02           120435
2024-03           127752
...
2024-12           125784
```

Try a complex query to see both agents merge into one labeled response:

```bash
python -m src.cli -q "Compare Q4 performance across regions and explain our code review process"
```

## Project layout

```
src/agents/       manager_agent.py, qualitative_agent.py, quantitative_agent.py
src/data/docs/    sample enterprise documents (security, code review, complaints)
src/db/           schema.sql, init_db.py (seeds SQLite sales/customers data)
src/cli.py        REPL + one-shot (-q) CLI entry point
src/llm_client.py Anthropic / OpenAI / offline-fallback LLM abstraction
tests/            unit tests for each agent + manager routing integration tests
```

## Rubric coverage

**Completion (baseline):** runs from a clean checkout on Python 3.11/3.12
with pinned-floor dependencies; CLI accepts a query and returns a
complete answer from all 3 agents (exceeds the "2 of 3" bar). All 8
milestones met: setup, Manager, Qualitative, Quantitative, multi-agent
integration, CLI, automated tests (19 passing), README + diagram.


## Known gaps

- No FastAPI layer, structured logging, or `/health` endpoint.
- Manager classification is keyword-based, not LLM-based.
