# 🚀 Deployment Runbook — one VM + Docker Compose

> Get the chatbot running **live 24/7** on a single small cloud VM, using the
> production stack in `docker-compose.prod.yml`. No domain, HTTPS, or webhook
> needed — the bot uses polling (outbound), so it works behind any VM.

See also: [CLOUD.md](CLOUD.md) (provider options & the Cloud Run alternative).

---

## Why a VM (not Cloud Run)

The app has a **persistent polling bot** + **3 stateful stores** (Redis,
Postgres, Qdrant). That's a stateful workload — a VM running Docker Compose is
simpler and cheaper than serverless + 3 managed databases. Deploy = the same
`docker compose up` you run locally.

---

## Step 1 — Pick a VM (free options)

| Provider | Free offer | Notes |
|---|---|---|
| **Oracle Cloud** | "Always Free" ARM VM (up to 4 CPU / 24 GB) | Best free tier; free forever |
| **GCP** | e2-micro free tier + $300 / 90-day credit | Good if you want GCP experience |
| **AWS** | t2.micro/t3.micro 12-month free | Fine too |

Pick **Ubuntu 22.04 LTS**. Minimum ~2 GB RAM (4 GB comfortable — the embedding
model + stores need room). Open only SSH (port 22) inbound; nothing else is
required because the bot is outbound-only.

## Step 2 — Install Docker on the VM

SSH in, then:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER          # then log out/in so `docker` works without sudo
```

## Step 3 — Get the code

```bash
git clone https://github.com/shanmugamani1023/retail-ai-chatbot.git
cd retail-ai-chatbot
```

## Step 4 — Create the .env (secrets)

`.env` is NOT in the repo, so create it on the VM:
```bash
cp .env.example .env
nano .env
```
Set at least:
```
GROQ_API_KEY=gsk_...
TELEGRAM_BOT_TOKEN=123456:AA...
POSTGRES_PASSWORD=change_me_to_something_strong
```
(Leave `TELEGRAM_MODE=polling`. The store URLs are overridden by the prod
compose file, so their values here don't matter.)

## Step 5 — Build & start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
This starts: `postgres`, `redis`, `qdrant`, `api`, `bot`. First build takes a
few minutes (installs PyTorch/embeddings).

## Step 6 — Ingest the catalog (once)

```bash
docker compose -f docker-compose.prod.yml run --rm api python -m src.ingest
```

## Step 7 — Verify

```bash
docker compose -f docker-compose.prod.yml ps          # all services Up
docker compose -f docker-compose.prod.yml logs -f bot # should show "Application started"
```
Then message your bot on Telegram — it now answers 24/7, even with your laptop off. 🎉

---

## Operations

```bash
# view logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f bot

# update after a git push
git pull
docker compose -f docker-compose.prod.yml up -d --build

# re-ingest an updated catalog
docker compose -f docker-compose.prod.yml run --rm api python -m src.ingest

# stop / start
docker compose -f docker-compose.prod.yml down          # stop (keep data)
docker compose -f docker-compose.prod.yml up -d          # start again
```

## Hardening (later)

- Set a strong `POSTGRES_PASSWORD` (already parameterized).
- Restrict the VM firewall to SSH only (default here — nothing else is exposed).
- Add log rotation / a monitoring agent.
- If you later want a public `/chat` API or a website, add Nginx + TLS and
  switch the bot to `TELEGRAM_MODE=webhook` (see CLOUD.md).

## The Cloud Run alternative (if you specifically want serverless)

Cloud Run needs: the API as a container + **managed** Redis (Memorystore),
Postgres (Cloud SQL), Qdrant (Qdrant Cloud), **and** switching the bot to
webhook mode (Cloud Run scales to zero, so it can't poll). More setup and cost.
Documented in [CLOUD.md](CLOUD.md); the VM path above is recommended for the MVP.
