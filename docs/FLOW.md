# 🛒 Autonomous Retail AI Chatbot — Flow & Architecture

> A memory-aware, agentic retail assistant on Telegram.
> Customers ask about products in natural language; the bot answers using an
> LLM agent that decides whether to look up **exact facts** (SQL) or
> **descriptions/recommendations** (semantic search), and remembers the
> conversation per user.

**Owner:** Shanmugamani · **Status:** Design locked, pre-build
**Target MVP:** production-shaped, running locally · **Future:** deploy to GCP Cloud Run

---

## 1. What we're building (one paragraph)

A customer messages our bot on **Telegram**. The message reaches our server, which
loads that customer's **conversation memory**, then hands the question to a
**tool-calling LLM agent**. The agent decides which tool to use:
`query_inventory_sql` (exact counts/prices/stock from **PostgreSQL**) or
`search_products` (descriptions/recommendations via **RAG** over **Qdrant**).
It can call one, both, or neither (if memory already answers). The agent writes a
natural reply, we save the turn to memory, and send the answer back to Telegram.

---

## 2. Tech Stack — every tool and *why*

| Layer | Tool | Why this one |
|---|---|---|
| Messaging | **Telegram** (`python-telegram-bot`) | Free, instant bot creation, great API; realistic retail channel |
| API / server | **FastAPI** (Uvicorn) | Async, fast, production-standard; stateless so it scales |
| Orchestration | **LangChain (LCEL + agents)** | Tool-calling agent, memory, RAG — the core skill |
| Agent brain (LLM) | **Groq** — `llama-3.3-70b-versatile` | Free tier, very fast, supports tool-calling; no GPU needed |
| Embeddings | **`sentence-transformers/all-MiniLM-L6-v2`** | Free, runs on CPU, industry-standard starter; text → 384-dim vectors |
| Vector store (RAG) | **Qdrant** | Production-grade, runs as a service, concurrent, scales; free & open source |
| Structured DB | **PostgreSQL** | Exact facts, concurrent writes, network-shared; production standard |
| Memory / cache | **Redis** | Fast shared session store; survives restarts; TTL auto-expiry |
| Packaging | **Docker + docker-compose** | Same image on laptop & cloud (dev/prod parity) |
| Observability | **LangSmith + structured logs** | Trace the agent's tool choices; debug & monitor |
| Cloud (future) | **GCP Cloud Run** | Container deploy, autoscale-to-zero, free HTTPS URL |

> **Swap note:** the vector store is abstracted by LangChain — **ChromaDB** can
> replace Qdrant in ~3 lines if maximum simplicity is preferred. Qdrant is chosen
> here for production readiness and dev/prod parity.

---

## 3. The three data stores (different jobs, don't confuse them)

| Store | Holds | Answers | Powered by | Changes |
|---|---|---|---|---|
| **Qdrant** | vectors of product *descriptions* | "good for dry hair?", "recommend…", "describe…" | all-MiniLM | rarely (descriptions) |
| **PostgreSQL** | stock, price, exact fields | "how many?", "cheapest?", "total?", "under ₹X?" | SQL | constantly (live stock) |
| **Redis** | conversation history per user | (not queried by agent) enables multi-turn memory | keyed by `chat_id` | every turn |

**Rule of thumb:** meaning → Qdrant · exact numbers/math → Postgres · who-said-what → Redis.

---

## 4. Ingestion Flow (setup-time; also on `/upload-catalog`)

Runs once to prepare the knowledge. **No LLM involved.** One CSV → two stores.

```
products.csv
    │
    ├──► chunk ──► embed (all-MiniLM) ──► vectors ──► Qdrant     (semantic search)
    │
    └──► load rows as-is ─────────────────────────► PostgreSQL  (exact facts)
```

- **Qdrant** gets the *descriptions* turned into vectors (for meaning search).
- **Postgres** gets the *structured rows* (name, price, stock) for exact queries.

---

## 5. Runtime Flow (every customer message)

```
 ① Customer types in Telegram
        │  "how many HP bottles?"
        ▼
 ② Message reaches our server
        • PROD: Telegram → webhook (HTTPS POST) → our endpoint
        • DEV : our bot long-polls Telegram ("any messages?")
        │  we read:  text + chat_id
        ▼
 ┌─────────────────── FastAPI /chat (stateless) ───────────────────┐
 │                                                                  │
 │  ③ LOAD memory for chat_id ───────────────► Redis  (load-or-create, append later)
 │                    │                                             │
 │                    ▼                                             │
 │  ④ ┌────────────────────────────┐                               │
 │    │  AGENT  (Groq LLM)          │  reads question + memory      │
 │    │  "which tool do I need?"    │  + tool docstrings            │
 │    └───────────────┬────────────┘                               │
 │                    │ decides via tool-calling                   │
 │          ┌─────────┴──────────┐                                 │
 │          ▼                    ▼                                 │
 │   🔧 query_inventory_sql   🔧 search_products                    │
 │        │  SQL on           │  vector search on                  │
 │        ▼  PostgreSQL       ▼  Qdrant (RAG)                       │
 │     exact rows          matching descriptions                   │
 │          └─────────┬──────────┘                                 │
 │                    ▼                                             │
 │  ⑤ tool result returns to the agent                             │
 │                    │  (agent may loop back to ④ for another tool)│
 │                    ▼                                             │
 │  ⑥ agent writes the final natural-language answer ──► Groq       │
 │                    │                                             │
 │  ⑦ SAVE this turn to memory ──────────────► Redis                │
 └────────────────────┬─────────────────────────────────────────────┘
                       │ { answer }
                       ▼
 ⑧ SEND answer back to customer ──► Telegram sendMessage API ──► phone
```

**Agent loop (steps ④–⑥):** `think → pick tool → run tool → read result → (enough? answer : pick another tool)`

---

## 6. How the agent decides (the "router" replacement)

There is **no hand-written router**. The LLM's tool-calling ability *is* the router.
It reads each tool's **docstring** and picks. Writing good docstrings = writing the router.

```python
@tool
def query_inventory_sql(query: str) -> str:
    """Get EXACT counts, stock levels, or prices from the inventory database.
    Use for: how many, total stock, cheapest, price of, items under ₹X."""

@tool
def search_products(query: str) -> str:
    """Search product DESCRIPTIONS for recommendations or features.
    Use for: 'good for dry hair', 'recommend a soda', 'tell me about X'."""
```

### Examples
| Customer question | Tool(s) the agent picks | Why |
|---|---|---|
| "how many HP bottles?" | `query_inventory_sql` | exact count → SQL |
| "which shampoo for dandruff?" | `search_products` | meaning → RAG |
| "dandruff shampoo under ₹100" | **both** | RAG for match + SQL for price filter |
| "how many are left?" (after asking about HP) | `query_inventory_sql` + **memory** | memory resolves "them" = HP |

---

## 7. Memory — how multi-turn works

Memory = a per-user list of past messages, stored in Redis, keyed by `chat_id`.

```python
redis["chat_12345"] = [
    HumanMessage("tell me about HP shampoo"),
    AIMessage("HP shampoo is anti-dandruff, ₹85, in stock"),
    HumanMessage("how many are left?"),
    AIMessage("23 left"),
]
```

- **Loaded** before the agent runs, **appended** after it answers.
- Each `chat_id` is isolated → customers never see each other's context.
- Lets the agent resolve "it / them / that one / how many left" against earlier turns.
- **TTL** (e.g. 24h) auto-expires idle sessions so Redis self-cleans.

---

## 8. Why each production choice (failure case / efficiency)

| Choice | Naive alternative | Failure / inefficiency it prevents |
|---|---|---|
| **Redis memory** | in-RAM dict | crash wipes all chats; multi-worker "forgets"; memory leak → OOM |
| **PostgreSQL** | SQLite file | write-locks under concurrency; can't be shared across servers |
| **Qdrant** | local Chroma file | not shared/concurrent-safe; no replication; won't scale |
| **Webhook (prod)** | polling only | polling wastes cycles; can't scale behind a load balancer |
| **LLM retry + fallback** | single bare call | one Groq blip → failed customer reply |
| **Background queue** | process in webhook | slow agent → Telegram times out → duplicate replies |
| **Semantic cache** | recompute every time | 100 identical questions = 100× cost & latency |
| **Observability** | print statements | can't see *why* the agent picked a tool; blind to 2am errors |
| **Docker** | "works on my machine" | dev/prod drift; painful deploys |

---

## 9. Dev vs Prod — what runs where

| | Development (your laptop) | Production (cloud) |
|---|---|---|
| Server | **your laptop** = the server | GCP Cloud Run |
| Telegram method | **polling** (no URL needed) | **webhook** (HTTPS push) |
| Public URL / tunnel | not needed | free HTTPS from Cloud Run |
| Redis / Postgres / Qdrant | Docker on laptop | managed or self-hosted VM |
| LLM (Groq) | over internet (free) | same |
| **Cost** | **₹0** | ₹0–cheap (see §11) |

**One config flag** (`TELEGRAM_MODE=polling|webhook`) switches between them — no code change.
This is possible because the app is **containerized, config-driven, and stateless** (12-factor).

Local dev loop:
```bash
docker-compose up          # Redis + Postgres + Qdrant on the laptop
python api/main.py         # FastAPI on localhost:8000
python bot/telegram_bot.py # polling — chat with the bot from your phone
```

---

## 10. Repository structure

```
retail-ai-chatbot/
├── data/products.csv          # sample catalog (~30 rows)
├── src/
│   ├── config.py              # settings + secrets from env (12-factor)
│   ├── ingest.py              # CSV → Qdrant + Postgres
│   ├── tools.py               # query_inventory_sql + search_products
│   ├── agent.py               # tool-calling agent + Redis memory
│   └── llm.py                 # Groq client + retry/fallback
├── api/main.py                # FastAPI: /chat /upload-catalog /health /ready
├── bot/telegram_bot.py        # polling (dev) / webhook (prod) via config
├── docker-compose.yml         # Redis + Postgres + Qdrant (+ API)
├── Dockerfile
├── .env.example
├── requirements.txt
├── FLOW.md                    # this document
└── README.md
```

---

## 11. Cost

**Development: ₹0.** All software is open source and runs locally; Groq + Telegram are free.

**Production — two paths:**
- **Path A — self-host (cheapest):** run the Docker stack on one free VM
  (**Oracle Cloud "Always Free"**, or **GCP $300 credit / e2-micro**). ≈ **₹0** at portfolio scale.
- **Path B — managed (easier, small cost):** GCP Cloud Run (free when idle) +
  Qdrant Cloud (free 1 GB) + Cloud SQL/Memorystore (~$10–25/mo).

> Free-tier limits change over time — re-verify at deploy time (Phase 4).

---

## 12. Future Cloud Plan (GCP — Phase 4)

**Why GCP Cloud Run:** deploy a container, autoscale to zero (pay ~nothing idle),
free HTTPS URL (so the Telegram webhook "just works"), simplest for a solo dev.

### Local → Cloud service mapping
| Local (Docker) | 🟦 GCP | 🟧 AWS | 🟦 Azure |
|---|---|---|---|
| FastAPI container | **Cloud Run** | App Runner / ECS Fargate | Container Apps |
| Redis | Memorystore | ElastiCache | Cache for Redis |
| PostgreSQL | Cloud SQL | RDS | Database for PostgreSQL |
| Qdrant | Qdrant Cloud / GKE | Qdrant Cloud / ECS | Qdrant Cloud / ACA |
| TLS / HTTPS | built into Cloud Run | ALB + ACM | built into Container Apps |
| Secrets | Secret Manager | Secrets Manager | Key Vault |
| Groq (LLM) | unchanged (external API) | same | same |

### What changes at deploy (no app-logic changes)
1. Build & push the Docker image to the registry (Artifact Registry).
2. Point env vars at cloud Redis / Postgres / Qdrant.
3. Move secrets `.env` → Secret Manager.
4. Flip `TELEGRAM_MODE: polling → webhook` and register the Cloud Run URL.
5. Add CI/CD (GitHub Actions) → auto-deploy on push to `main`.

---

## 13. Build Plan (phases)

| Phase | Goal | Key deliverables |
|---|---|---|
| **0 — Setup** | cloud-portable foundation | repo, docker-compose (Redis+Postgres+Qdrant), config/env, Groq key, BotFather token, sample `products.csv`, skeleton |
| **1 — Ingestion + tools** | fill the stores, define tools | CSV → Qdrant + Postgres; `search_products` (RAG) + `query_inventory_sql` |
| **2 — Agent + backend** | the brain | tool-calling agent, Redis memory, LLM retry/fallback, FastAPI `/chat /health /ready`, rate limiting |
| **3 — Telegram + observability** | the face + eyes | polling(dev)/webhook(prod) bot, LangSmith + structured logs, demo video, README, push to GitHub |
| **4 — Cloud deploy (future)** | go live | GCP Cloud Run, managed/self-hosted stores, secrets, webhook, CI/CD, monitoring |

---

## 14. Glossary

- **Webhook** — a URL on our server that Telegram POSTs messages to the instant they arrive (production). Not a tunnel.
- **Polling** — our server repeatedly asks Telegram "any messages?" (used in dev; no public URL needed).
- **RAG** — Retrieve-Augment-Generate: search relevant text, add to the prompt, let the LLM answer grounded in it.
- **Embedding** — a list of numbers representing text meaning; similar meaning → nearby numbers. Made by all-MiniLM.
- **Vector database (Qdrant)** — stores embeddings and finds the closest ones fast (semantic search).
- **Tool-calling agent** — an LLM given a set of tools that decides itself which to call to answer a question.
- **Memory** — per-user conversation history (in Redis) fed back to the LLM each turn for multi-turn context.
- **Stateless app** — keeps no state in itself; all state lives in Redis/Postgres/Qdrant → can run many copies.
- **12-factor** — app design (containerized, config via env, stateless) that makes cloud deployment a config change, not a rewrite.
- **MVP** — Minimum Viable Product: the leanest version that works and is demoable; polish comes later.

---

*Design locked. Next step: Phase 0 — scaffold the project.*
