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
| **[docs/CLOUD.md](docs/CLOUD.md)** | GCP-first deployment plan, service mapping, cost paths, deploy checklist |
| **[docs/STRUCTURE.md](docs/STRUCTURE.md)** | Every folder & file explained, with use cases and status |

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

> Full setup lands in Phase 0 (see [docs/SCHEDULE.md](docs/SCHEDULE.md)).

```bash
# 1. clone
git clone https://github.com/<user>/retail-ai-chatbot.git
cd retail-ai-chatbot

# 2. secrets
cp .env.example .env        # add GROQ_API_KEY and TELEGRAM_BOT_TOKEN

# 3. start data stores
docker-compose up -d        # Redis + Postgres + Qdrant

# 4. ingest sample catalog
python -m src.ingest

# 5. run API + bot
python api/main.py
python bot/telegram_bot.py  # polling — message your bot from Telegram
```

---

## 📊 Status

🚧 **In development** — see the progress tracker in [docs/SCHEDULE.md](docs/SCHEDULE.md).

## 📄 License

MIT
