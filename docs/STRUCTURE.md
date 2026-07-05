# 📂 Project Structure — Folders & Files Explained

> A complete guide to every folder and file in the Retail AI Chatbot, what it
> does, why it exists, and its current status. Read this to understand the
> layout before touching the code.

See also: [FLOW.md](FLOW.md) (architecture) · [SCHEDULE.md](SCHEDULE.md) (plan) · [CLOUD.md](CLOUD.md) (deploy).

---

## 1. The big picture

The project separates into **layers** — each folder does exactly one job.
This "separation of concerns" means you can change one layer without breaking
the others (e.g. swap the database without touching the Telegram code).

```
retail-ai-chatbot/
├── src/       🧠 the brain   — core logic (config, ingestion, tools, agent, LLM)
├── api/       🔌 the door    — FastAPI web server (endpoints)
├── bot/       💬 the face    — Telegram interface
├── data/      📦 the fuel    — the product catalog (CSV)
├── docs/      📚 the manual  — planning & reference documents
├── scripts/   🛠️ helpers     — handy SQL / utility scripts
└── (root)     ⚙️ the setup   — dependencies, Docker, config templates
```

**Mental model:**
`src/` thinks · `api/` serves · `bot/` talks · `data/` feeds · `docs/` explains · root configures.

**Data flow across the folders:**
```
Customer → bot/ (Telegram) → api/ (FastAPI) → src/ (agent + tools + memory)
                                                   ↓
                              data/ → ingested into → Qdrant + Postgres + Redis
```

---

## 2. Status legend

| Symbol | Meaning |
|---|---|
| ✅ | Implemented & working |
| 🔨 | Stub / placeholder (filled in a later phase) |

---

## 3. `src/` — core logic (the brain)

Everything that *thinks* lives here.

| File | Use case | Status |
|---|---|---|
| `config.py` | Central settings. Reads everything (DB URLs, API keys, model names, tuning) from environment / `.env`. One place for all config — this is what makes moving to the cloud a config change, not a rewrite. | ✅ |
| `ingest.py` | The ingestion pipeline. Loads `data/products.csv`, writes structured rows to **PostgreSQL**, and embeds product descriptions into **Qdrant**. Run with `python -m src.ingest`. | ✅ |
| `tools.py` | The two agent tools: `search_products` (semantic search / RAG over Qdrant) and `query_inventory_sql` (read-only SQL over Postgres, grounded with real categories + matching tips). Their **docstrings** are what the agent reads to decide which to call. | ✅ |
| `llm.py` | Groq LLM client (`openai/gpt-oss-20b`) with timeout + retry; `gpt-oss-120b` as fallback model. | ✅ |
| `agent.py` | The tool-calling agent (LangChain v1 `create_agent`) + system prompt; wires per-session (chat_id) memory in Redis via `RedisChatMessageHistory`; `answer(message, session_id)` is the one entry point. | ✅ |
| `ratelimit.py` | Fixed-window per-session rate limiting in Redis (N messages / window). | ✅ |
| `__init__.py` | Empty file marking `src/` as a Python package, so `from src.config import settings` works. | ✅ |

---

## 4. `api/` — web server (the door)

The FastAPI backend: the entry point that receives requests and returns answers.

| File | Use case | Status |
|---|---|---|
| `main.py` | HTTP endpoints: `GET /health` (liveness), `GET /ready` (pings Redis+Postgres+Qdrant), `POST /chat` (routes through the agent, with rate limiting), `POST /upload-catalog` (re-ingest). | ✅ |
| `__init__.py` | Marks `api/` as a Python package. | ✅ |

---

## 5. `bot/` — Telegram interface (the face)

The layer customers actually touch. Thin by design — it just shuttles messages
between Telegram and the API.

| File | Use case | Status |
|---|---|---|
| `telegram_bot.py` | Receives Telegram messages, forwards them to the API's `/chat` (using the Telegram `chat_id` as the `session_id`), and sends replies back. Typing indicator + long-message splitting. Polling in dev, webhook in prod (chosen by config). | ✅ |
| `__init__.py` | Marks `bot/` as a Python package. | ✅ |

---

## 6. `data/` — the catalog (the fuel)

| File | Use case | Status |
|---|---|---|
| `products.csv` | 30 sample retail products (id, name, category, brand, price, stock, unit, description). This is the **source** that ingestion loads into Postgres + Qdrant. Edit this to change the catalog. | ✅ |

---

## 7. `scripts/` — helper scripts

| File | Use case | Status |
|---|---|---|
| `explore.sql` | Ready-to-run SQL queries to explore the catalog in a DB tool (VS Code PostgreSQL extension, DBeaver, etc.). Useful for seeing what `query_inventory_sql` works against. | ✅ |

---

## 8. `docs/` — documentation (the manual)

| File | Use case |
|---|---|
| `FLOW.md` | Full architecture, complete data flow, why each choice, glossary. |
| `SCHEDULE.md` | Dated build plan (Jul 4 → Jul 24 MVP), milestones, progress tracker. |
| `CLOUD.md` | GCP-first deployment plan, service mapping, cost paths, deploy checklist. |
| `STRUCTURE.md` | This file — folders & files explained. |

---

## 9. Root config files (the setup)

| File | Use case | Why it exists |
|---|---|---|
| `README.md` | Project landing page shown on GitHub. | First thing anyone sees. |
| `requirements.txt` | The list of Python libraries (`pip install -r requirements.txt`). | Reproducible environment. |
| `.env.example` | Template of required config/secrets (Groq key, bot token, DB URLs). Copy to `.env` and fill in. | Shows needed config without exposing real secrets. |
| `docker-compose.yml` | Defines the 3 data-store containers (Redis, Postgres, Qdrant). `docker compose up -d` starts them all. | One command runs the whole data layer. |
| `Dockerfile` | Recipe to package the *app* (FastAPI) into a container. | Used for cloud deploy (Phase 4). |
| `.dockerignore` | Files to exclude from the Docker image build (`.venv`, docs, etc.). | Smaller, faster images. |
| `.gitignore` | Files git must never track (secrets, `.venv`, data volumes, caches). | Keeps secrets & junk out of GitHub. |

---

## 10. What is NOT in the repo (and why)

These exist on your machine but are deliberately excluded by `.gitignore`:

| Item | Why excluded |
|---|---|
| `.venv/` | Your Python virtual environment — large, machine-specific. Others recreate it from `requirements.txt`. |
| `.env` | Your **real secrets** — must never reach GitHub. Only `.env.example` is shared. |
| `__pycache__/` | Python's compiled cache — auto-generated. |
| `pip_install.log` | Install log — local noise. |
| Docker volumes (`postgres_data`, `redis_data`, `qdrant_storage`) | The actual database data — lives inside Docker (WSL2), not the repo. This is why data survives restarts. |

> **Key rule:** only source code + config templates go to GitHub. Secrets and
> generated/runtime data stay local.

---

## 11. Two different kinds of "data" (don't confuse them)

| | `data/products.csv` | Docker volumes |
|---|---|---|
| Contains | the **source** catalog | the **loaded/processed** data (rows, vectors, memory) |
| Lives in | the repo → GitHub | Docker → your machine only |
| In git? | ✅ yes (it's source) | ❌ no (runtime data) |
| You edit it? | ✅ yes | ❌ no (Docker manages it) |

`products.csv` is the **input**; the volumes hold the **output** after ingestion.

---

## 12. Quick command reference

```bash
# start / stop the data stores
docker compose up -d          # start Redis + Postgres + Qdrant
docker compose down           # stop, keep data
docker compose down -v        # stop AND wipe data (fresh start)

# ingest the catalog into Postgres + Qdrant
python -m src.ingest

# run the API (dev)
uvicorn api.main:app --reload     # or: python -m api.main

# run the Telegram bot (dev)
python -m bot.telegram_bot
```
