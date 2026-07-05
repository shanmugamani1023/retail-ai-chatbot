# 🛒 Autonomous Retail AI Chatbot

A memory-aware, **agentic** retail assistant on **Telegram**. Customers ask about
products in natural language; an **LLM tool-calling agent** decides whether to fetch
**exact facts** (SQL) or **descriptions/recommendations** (semantic search / RAG),
and remembers the conversation per user.

> Built with LangChain + Groq + Qdrant + PostgreSQL + Redis, containerized with
> Docker, and designed to deploy to **GCP Cloud Run** with a config change (not a rewrite).

---

## ✨ Features

- 🤖 **Tool-calling agent** — the LLM itself decides which tool to use (no hand-written router)
- 🔍 **RAG over Qdrant** — semantic search across product descriptions
- 🗄️ **SQL over PostgreSQL** — exact counts, prices, stock, and math
- 🧠 **Conversation memory (Redis)** — multi-turn, per-user context
- 💬 **Telegram** — polling in dev, webhook in production (one config flag)
- 🐳 **Dockerized** — same image on laptop and cloud
- ☁️ **Cloud-ready** — 12-factor design, deploy to GCP Cloud Run

---

## 🏗️ Architecture (at a glance)

```
Telegram → FastAPI → Agent (picks tools) → SQL (Postgres) / RAG (Qdrant) → answer
                        │
                     Memory (Redis, per chat_id)
```

Full details in **[docs/FLOW.md](docs/FLOW.md)**.

---

## 📚 Documentation

| Doc | What it covers |
|---|---|
| **[docs/FLOW.md](docs/FLOW.md)** | Complete architecture, data flow, tools, why each choice, glossary |
| **[docs/SCHEDULE.md](docs/SCHEDULE.md)** | Dated build plan (Jul 4 → Jul 24 MVP), milestones, progress tracker |
| **[docs/CLOUD.md](docs/CLOUD.md)** | Cloud options, service mapping, cost paths, Cloud Run alternative |
| **[docs/DEPLOY.md](docs/DEPLOY.md)** | Step-by-step runbook: deploy the full stack to one VM |
| **[docs/STRUCTURE.md](docs/STRUCTURE.md)** | Every folder & file explained, with use cases and status |
| **[docs/FUTURE.md](docs/FUTURE.md)** | Post-MVP roadmap: CI/CD, monitoring, fine-tuning, WhatsApp, scale |

---

## 🧰 Tech Stack

| Layer | Tool |
|---|---|
| Messaging | Telegram (`python-telegram-bot`) |
| API | FastAPI |
| Orchestration | LangChain (LCEL + agents) |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | Qdrant |
| Structured DB | PostgreSQL |
| Memory/cache | Redis |
| Packaging | Docker + docker-compose |

---

## 🚀 Quick start (dev)

```bash
# 1. clone
git clone https://github.com/shanmugamani1023/retail-ai-chatbot.git
cd retail-ai-chatbot

# 2. Python env + deps
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 3. secrets — get keys from console.groq.com/keys and @BotFather
cp .env.example .env              # then edit: GROQ_API_KEY, TELEGRAM_BOT_TOKEN

# 4. start data stores (Docker)
docker compose up -d              # Redis + Postgres + Qdrant

# 5. ingest the sample catalog -> Postgres + Qdrant
python -m src.ingest
```

Then run the **two processes** (separate terminals):

```bash
# Terminal 1 — the API (the brain)
uvicorn api.main:app --reload

# Terminal 2 — the Telegram bot (the face)
python -m bot.telegram_bot        # polling; message your bot on Telegram
```

Open Telegram, find your bot, send `/start`, and chat. 🎉

## 💬 Example conversation

```
You:  How many HP shampoos are in stock?
Bot:  There are 2 HP shampoos currently in stock.

You:  Recommend something for dandruff
Bot:  For dandruff, I'd suggest:
      - Head & Shoulders 340 ml – Rs.180, 40 in stock
      - HP Anti-Dandruff Shampoo – Rs.85, 47 in stock

You:  Tell me about Amul butter
Bot:  Amul Butter (100g) – Rs.56, in stock. Rich, creamy salted table butter...
You:  How many are left?
Bot:  There are 140 packs left in stock.        # ← remembered the context
```

---

## 🐳 Run the full stack in Docker

Run the **entire app** (API + bot + Redis + Postgres + Qdrant) in containers with
one command — the same setup used for deployment (`docker-compose.prod.yml`).
Requires a `.env` with `GROQ_API_KEY` and `TELEGRAM_BOT_TOKEN`.

```bash
cd retail-ai-chatbot

# build + start everything (5 containers)
docker compose -f docker-compose.prod.yml up -d --build

# ingest the catalog once (only needed the first time / after CSV changes)
docker compose -f docker-compose.prod.yml run --rm api python -m src.ingest
```

Then message your bot on Telegram — it's served entirely from Docker.

### Managing the stack

```bash
# status
docker compose -f docker-compose.prod.yml ps

# view logs (live)
docker compose -f docker-compose.prod.yml logs -f bot     # bot
docker compose -f docker-compose.prod.yml logs -f api     # API
docker compose -f docker-compose.prod.yml logs -f         # everything

# stop / start
docker compose -f docker-compose.prod.yml down            # stop (keeps data)
docker compose -f docker-compose.prod.yml up -d           # start again
docker compose -f docker-compose.prod.yml down -v         # stop AND wipe data
```

> Docker Desktop must be running. On Windows, if `docker` isn't found, ensure
> `C:\Program Files\Docker\Docker\resources\bin` is on your PATH.

For deploying this stack to a cloud VM, see **[docs/DEPLOY.md](docs/DEPLOY.md)**.

---

## 📊 Status

✅ **MVP working** — Telegram bot answers product questions via a tool-calling
agent (RAG + SQL) with conversation memory. See [docs/SCHEDULE.md](docs/SCHEDULE.md).
Next: cloud deployment (see [docs/CLOUD.md](docs/CLOUD.md)).

## 📄 License

MIT
