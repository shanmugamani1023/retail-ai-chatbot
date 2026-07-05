# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**Autonomous Retail AI Chatbot** — a memory-aware, agentic retail assistant on
Telegram. A customer messages the bot; a LangChain tool-calling agent (Groq LLM)
decides whether to fetch **exact facts** (SQL over Postgres) or
**descriptions/recommendations** (RAG over Qdrant), and remembers the
conversation per user (Redis). Built to deploy to GCP Cloud Run via config, not
a rewrite.

Status: **MVP working** (Phases 0–3 complete). Phase 4 (cloud deploy) is future.

## Architecture

```
Telegram → bot/ (polling dev / webhook prod) → api/ /chat → src/agent.py
                                                                 ↓ picks a tool
                                    query_inventory_sql (Postgres) | search_products (Qdrant/RAG)
                                                                 ↓
                                              Redis memory (per chat_id/session_id)
```

- **Agent has no hand-written router** — the LLM's tool-calling picks the tool.
  Tool **docstrings** in `src/tools.py` are what drive that choice; edit them to
  change routing behavior.
- **Two data stores, two jobs:** Postgres = exact facts (counts/prices/stock);
  Qdrant = meaning (descriptions/recommendations). Redis = conversation memory.

## Tech stack

- LLM: **Groq** `openai/gpt-oss-20b` (reliable tool-calling; fallback `gpt-oss-120b`).
  NOTE: `llama-3.3-70b-versatile` intermittently throws `tool_use_failed` — avoid for the agent.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local, 384-dim).
- Vector store: **Qdrant**. Structured DB: **PostgreSQL**. Memory/cache: **Redis**.
- Framework: **LangChain v1** (`from langchain.agents import create_agent`) — the
  old `AgentExecutor`/`create_tool_calling_agent` do NOT exist in v1.
- API: FastAPI. Bot: python-telegram-bot v21. Config: pydantic-settings.

## Commands

```bash
# data stores (Docker)
docker compose up -d            # start Redis + Postgres + Qdrant
docker compose down             # stop (keep data);  add -v to wipe data

# ingest catalog -> Postgres + Qdrant
python -m src.ingest

# run the app (two processes)
uvicorn api.main:app --reload   # API (the brain)
python -m bot.telegram_bot      # Telegram bot (the face)
```

- Python venv is at `.venv/`. On Windows use `.venv\Scripts\python.exe`.
- Docker CLI may not be on PATH; it's at
  `C:\Program Files\Docker\Docker\resources\bin`. Docker Desktop must be running.

## Config & secrets

- All config comes from env / `.env` via `src/config.py` (12-factor).
- `.env` is **gitignored** — never commit it. `.env.example` is the template.
- Required secrets: `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`.
- `TELEGRAM_MODE=polling` (dev) | `webhook` (prod) is the single dev/prod switch.

## Conventions

- Keep the layers separate: `src/` = logic, `api/` = HTTP, `bot/` = Telegram,
  `data/` = catalog CSV, `docs/` = documentation, `scripts/` = helper SQL.
- The SQL tool executes **read-only SELECT** only; keep it that way.
- Answers should be plain chat-friendly text (no markdown tables) — see the
  system prompt in `src/agent.py`.
- To change the catalog: edit `data/products.csv`, re-run `python -m src.ingest`.

## Docs

- `docs/FLOW.md` — architecture & data flow
- `docs/STRUCTURE.md` — every folder/file explained
- `docs/SCHEDULE.md` — build plan & progress
- `docs/CLOUD.md` — GCP deployment plan

## Known limitations (MVP)

- Text-to-SQL is fuzzy on vague concepts (e.g. "soda" may match only "cola").
  Exact/named queries are reliable. Improve via better SQL grounding or RAG+SQL.
- Memory & rate-limit live in Redis (good); catalog re-ingest is full-rebuild
  (`force_recreate`), fine for the sample size.
