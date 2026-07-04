# ☁️ Cloud Deployment Plan — Retail AI Chatbot (GCP-first)

> How the locally-built, containerized app goes live on the cloud.
> Because the app is **containerized, config-driven, and stateless (12-factor)**,
> deploying is a **config change, not a rewrite**.

See also: [FLOW.md](FLOW.md) (architecture) · [SCHEDULE.md](SCHEDULE.md) (timeline).
**Phase 4 window:** Aug 22 – Sep 4, 2026 (roadmap Week 9–10).

---

## 1. Guiding principle — why deploy is painless

Three design rules, followed from day one, make this work:

1. **Containerized (Docker)** — the exact same image runs on the laptop and the cloud.
2. **Config via environment variables** — DB URLs, API keys, polling-vs-webhook all come from env. Cloud = swap env values, touch zero code.
3. **Stateless app + external state** — all state lives in Redis / Postgres / Qdrant, so we can run 1 copy locally or N copies in the cloud with the same code.

---

## 2. Recommended target: GCP Cloud Run

**Why Cloud Run:**
- Deploy a container directly — no server management.
- **Autoscales to zero** → pay ~nothing when idle (ideal for a portfolio project).
- **Free HTTPS URL** out of the box → the Telegram **webhook just works** (no separate Nginx/cert).
- Simplest of the big-3 clouds for a solo developer.

---

## 3. Local → Cloud service mapping (all 3 providers)

| Local (Docker) | 🟦 GCP | 🟧 AWS | 🟦 Azure |
|---|---|---|---|
| FastAPI container | **Cloud Run** ⭐ | App Runner / ECS Fargate | Container Apps |
| Redis (memory/cache) | Memorystore | ElastiCache | Cache for Redis |
| PostgreSQL (inventory) | Cloud SQL | RDS | Database for PostgreSQL |
| Qdrant (vectors) | Qdrant Cloud / GKE | Qdrant Cloud / ECS | Qdrant Cloud / ACA |
| TLS / HTTPS | built into Cloud Run | ALB + ACM | built into Container Apps |
| Secrets | Secret Manager | Secrets Manager | Key Vault |
| Image registry | Artifact Registry | ECR | ACR |
| CI/CD | Cloud Build / GitHub Actions | GitHub Actions | GitHub Actions |
| Groq (LLM) | *unchanged — external API* | same | same |

---

## 4. Two deployment paths (by cost)

### Path A — Self-host on one VM (cheapest, ≈ ₹0)
Run the same `docker-compose` stack on a single cloud VM.
- **Oracle Cloud "Always Free"** — free forever (~4 CPU / 24 GB ARM). Best free option.
- **GCP** — `e2-micro` free tier + **$300 credit / 90 days** for new accounts.
- Add Nginx + Let's Encrypt for HTTPS (needed for the webhook).
- Best when: portfolio scale, cost = priority.

### Path B — Managed services (easier, ~$10–25/mo)
Let the cloud run each database (backups, scaling handled for you).
- GCP Cloud Run (free when idle) + Qdrant Cloud (free 1 GB) + Cloud SQL + Memorystore.
- Best when: you want zero infra maintenance / real traffic.

> Free-tier limits change over time — re-verify current offers at deploy time.

---

## 5. What changes at deploy (checklist — no app-logic changes)

- [ ] **Build & push image** to Artifact Registry
      `docker build -t <registry>/retail-bot . && docker push ...`
- [ ] **Provision stores** — Redis, Postgres, Qdrant (managed or on the VM)
- [ ] **Set env vars** on Cloud Run → point at the cloud store URLs
- [ ] **Move secrets** `.env` → **Secret Manager** (Groq key, bot token, DB creds)
- [ ] **Deploy** the container to Cloud Run → get the HTTPS URL
- [ ] **Flip Telegram mode** `TELEGRAM_MODE: polling → webhook`
- [ ] **Register webhook** → `setWebhook` with the Cloud Run URL
- [ ] **Add CI/CD** — GitHub Actions: on push to `main` → build → deploy
- [ ] **Add monitoring** — Sentry (errors) + Cloud Run metrics (latency, cost)
- [ ] **Smoke test** — message the bot; confirm end-to-end reply

---

## 6. Config: the single dev/prod switch

Everything that differs between laptop and cloud is env-driven:

```env
# --- dev (laptop) ---
TELEGRAM_MODE=polling
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://localhost:5432/retail
QDRANT_URL=http://localhost:6333

# --- prod (cloud) — same keys, different values ---
TELEGRAM_MODE=webhook
WEBHOOK_URL=https://retail-bot-xxxx.run.app/telegram/webhook
REDIS_URL=redis://<memorystore-ip>:6379
POSTGRES_URL=postgresql://<cloud-sql-conn>/retail
QDRANT_URL=https://<cluster>.qdrant.cloud
```

No code branches on "am I in the cloud?" — it just reads env.

---

## 7. Production architecture (deployed)

```
                     Customer (Telegram)
                           │  webhook (HTTPS)
                           ▼
                   ┌─────────────────┐
                   │  Cloud Run       │  auto HTTPS + autoscale
                   │  (FastAPI, N     │  (stateless replicas)
                   │   instances)     │
                   └───────┬─────────┘
             ┌─────────────┼──────────────┬──────────────┐
             ▼             ▼              ▼              ▼
        Memorystore    Cloud SQL      Qdrant Cloud    Groq API
        (Redis)        (Postgres)     (vectors)       (LLM, external)

   Secrets: Secret Manager   |   Monitoring: Cloud Run metrics + Sentry
   CI/CD: GitHub Actions → build image → deploy to Cloud Run on push to main
```

---

## 8. Rollout order (safe sequence)

1. Provision + verify each store independently (connect from laptop first).
2. Deploy the container with **polling** still on → confirm the app boots in the cloud.
3. Switch to **webhook**, register URL → confirm live messages.
4. Wire CI/CD last, once manual deploy is proven.
5. Add monitoring/alerts.

> Change one thing at a time — never flip stores + webhook + CI/CD together.
