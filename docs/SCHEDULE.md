# 📅 Build Schedule — Retail AI Chatbot

> Zero → shipped MVP → cloud. Built around availability of
> **weekdays 1–2 hrs, weekends 4–6 hrs**. Start: **Sat, Jul 4, 2026**.
> MVP target: **Fri, Jul 24, 2026**.

See also: [FLOW.md](FLOW.md) (architecture) · [CLOUD.md](CLOUD.md) (deployment).

---

## Effort estimate per phase

| Phase | Work | Est. hours |
|---|---|---|
| 0 — Setup | repo, Docker stack, config, sample data | ~5 |
| 1 — Ingestion + tools | CSV → Qdrant + Postgres, 2 tools | ~10 |
| 2 — Agent + backend | agent, Redis memory, FastAPI, retry/rate-limit | ~14 |
| 3 — Telegram + ship | bot, observability, README, demo, push | ~12 |
| **MVP total (0–3)** | | **~41** |
| 4 — Cloud (future) | GCP deploy, CI/CD, monitoring | ~12 |

Available time Jul 4–24 ≈ **50 hrs** → comfortable fit with buffer.

---

## Week A — Jul 4–10 · Foundation + Ingestion (Phases 0 → 1)

| Date | Day | Hrs | Focus |
|---|---|---|---|
| **Jul 4** | Sat | 5 | **Phase 0:** repo, `docker-compose` (Redis+Postgres+Qdrant), config/env, `requirements.txt`, Groq key, BotFather token, sample `products.csv`. ✅ `docker-compose up` works |
| **Jul 5** | Sun | 5 | **Phase 1a:** `ingest.py` — CSV → embed (all-MiniLM) → Qdrant; rows → Postgres. ✅ data verified in both stores |
| Jul 6–10 | Mon–Fri | 1.5 ea | **Phase 1b:** `tools.py` — `search_products` (RAG) + `query_inventory_sql`; test each tool standalone; notes on RAG vs fine-tuning |

**End of Week A:** data loaded; both tools return correct results when called directly.

---

## Week B — Jul 11–17 · The Brain (Phase 2)

| Date | Day | Hrs | Focus |
|---|---|---|---|
| **Jul 11** | Sat | 5 | **Phase 2a:** tool-calling agent (`create_tool_calling_agent`), wire both tools, verbose logging; test tool selection |
| **Jul 12** | Sun | 5 | **Phase 2b:** Redis memory per `chat_id`; test multi-turn ("how many are left?") |
| Jul 13–17 | Mon–Fri | 1.5 ea | **Phase 2c:** FastAPI `/chat /health /ready`, LLM retry/fallback, rate limiting; test with curl |

**End of Week B:** working API — `curl /chat` gives grounded, multi-turn answers via the agent.

---

## Week C — Jul 18–24 · The Face + Ship (Phase 3)

| Date | Day | Hrs | Focus |
|---|---|---|---|
| **Jul 18** | Sat | 5 | **Phase 3a:** `telegram_bot.py` polling → `/chat`, `chat_id`→session, `/start`, typing indicator, long-message split. ✅ test on phone |
| **Jul 19** | Sun | 5 | **Phase 3b:** LangSmith tracing + structured logs; polish prompts; handle edge cases |
| Jul 20–23 | Mon–Thu | 1.5 ea | README + architecture diagram, `.env.example`, cleanup, **record demo video** |
| **Jul 24** | Fri | 2 | Final push to GitHub, add to portfolio. 🎉 **MVP milestone hit** |

**End of Week C:** live, demoable Telegram bot on GitHub with README + demo video.

---

## Phase 4 — Cloud Deploy · Future (Aug 22 – Sep 4)

Aligns with roadmap Week 9–10. Same containers, config change only. Details in [CLOUD.md](CLOUD.md).

| Window | Focus |
|---|---|
| Aug 22–28 | Deploy Docker image to **GCP Cloud Run**; managed/self-hosted Redis+Postgres+Qdrant; secrets → Secret Manager; flip polling→**webhook** |
| Aug 29–Sep 4 | **CI/CD** (GitHub Actions auto-deploy), Nginx/TLS if self-hosting, Sentry + basic monitoring; live URL on resume |

---

## Milestone checkpoints

| Date | Milestone |
|---|---|
| Jul 5 (Sun) | Data flowing into Qdrant + Postgres |
| Jul 12 (Sun) | Agent picks tools + remembers conversation |
| Jul 17 (Fri) | Backend API fully working |
| **Jul 24 (Fri)** | **MVP shipped: Telegram bot live on GitHub + demo** |
| Sep 4 | Deployed to GCP with live URL + CI/CD |

---

## Weekly rules (non-negotiable)

- Weekdays: 1–2 hrs after work — small coding tasks.
- Weekend: 4–6 hrs — build features, push code.
- Every Sunday: review the week, update GitHub, tick this checklist.

---

## Progress tracker

- [ ] Phase 0 — Setup (Jul 4)
- [ ] Phase 1 — Ingestion + tools (Jul 5–10)
- [ ] Phase 2 — Agent + backend (Jul 11–17)
- [ ] Phase 3 — Telegram + ship (Jul 18–24)
- [ ] **MVP shipped (Jul 24)**
- [ ] Phase 4 — Cloud deploy (Aug 22 – Sep 4)
