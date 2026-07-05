# 🔮 Future Enhancements & TODO

Post-MVP roadmap for the Retail AI Chatbot. Each epic lists the **goal**, a
**TODO checklist**, and **suggestions / how-to**. Ordered roughly by
value-for-effort at the bottom.

See also: [FLOW.md](FLOW.md) · [CLOUD.md](CLOUD.md) · [DEPLOY.md](DEPLOY.md)

---

## Epic 1 — CI/CD: automate the deploy pipeline

**Goal:** change code → push to GitHub → it builds, tests, and redeploys to the
VM automatically. No manual SSH each time.

**TODO**
- [ ] Add a GitHub Actions workflow (`.github/workflows/deploy.yml`)
- [ ] On push to `main`: build the image, run a quick smoke test
- [ ] Push the image to a registry (GitHub Container Registry / Artifact Registry)
- [ ] Auto-deploy to the VM (pull new image + `docker compose up -d`)
- [ ] Provision the VM reproducibly with **Terraform** (Infrastructure-as-Code)

**Suggestions / how**
- **Simplest first:** a GitHub Action that SSHes into the VM and runs
  `git pull && docker compose -f docker-compose.prod.yml up -d --build`.
  (Store the VM SSH key as a GitHub Secret.)
- **Better (image-based):** build in CI → push to **GHCR** → the VM pulls the
  tagged image. Faster deploys, no building on the VM. Add **Watchtower** on the
  VM to auto-pull new images.
- **Best (reproducible infra):** Terraform for the VM + firewall + IAM, so the
  whole environment can be recreated with one command.
- Secrets move from a hand-typed `.env` → **GCP Secret Manager** / GitHub Secrets.
- This is roadmap Week 10 ("GitHub Actions: auto-deploy on push").

---

## Epic 2 — Observability: monitor all prompts & answers

**Goal:** see every question, the tool the agent chose, the answer, latency, and
cost — so you can debug, measure quality, and spot issues.

**TODO**
- [ ] Wire **LangSmith** to trace every agent run (tool calls + reasoning)
- [ ] Log each turn to a `conversations` table in Postgres (question, answer,
      tool used, latency, session_id, timestamp)
- [ ] Capture user **feedback** (👍/👎 buttons in Telegram) per answer
- [ ] Metrics: response time, tool-usage mix, error rate, tokens/cost per query
      (**Prometheus + Grafana** dashboard)
- [ ] Error tracking with **Sentry**

**Suggestions / how**
- **Start with LangSmith** — set `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`;
  you instantly see every agent decision. Lowest effort, huge insight.
- Add a `conversations` table — this log becomes your **training/eval data** for
  Epic 3 (the data flywheel).
- Telegram inline 👍/👎 buttons give a cheap quality signal per answer.
- Redact PII before logging (privacy — see Epic 5).

---

## Epic 3 — Quality: evaluation, retraining & fine-tuning

**Goal:** measurably improve answer quality over time.

**TODO**
- [ ] Build an **evaluation set** (e.g. 50 real questions + expected answers)
- [ ] Add an **LLM-as-judge** eval to score answers on a schedule
- [ ] Improve prompts + RAG using failure cases (cheapest wins first)
- [ ] Curate a fine-tuning dataset from logged good conversations (Epic 2)
- [ ] Fine-tune an open model (LoRA) if prompt/RAG improvements plateau

**Suggestions / how (important reality check)**
- ⚠️ **You can't fine-tune Groq's hosted models directly.** So the practical
  ladder is:
  1. **Prompt engineering + better RAG** — 80% of quality gains, near-zero cost.
     Fix the "soda" fuzziness, add few-shot examples, tune chunking/top-k.
  2. **Evaluation harness** — measure before/after so "improvement" is real, not
     vibes. Use an LLM-as-judge over your eval set.
  3. **Fine-tuning (only if needed):** collect Q&A pairs → fine-tune an open
     model (Llama/Mistral) with **LoRA** → host it on a provider that serves
     custom models (Together, Fireworks, Replicate, or your own GPU). Groq won't
     host your fine-tune, so this changes the LLM backend.
- **Data flywheel:** monitoring (Epic 2) → curate data → eval → improve → repeat.
- For retail, **RAG improvements usually beat fine-tuning** — the knowledge lives
  in the catalog, not the model weights.

---

## Epic 4 — WhatsApp channel (multi-channel)

**Goal:** the same chatbot brain answering on WhatsApp too (more realistic for
retail — customers already use WhatsApp).

**TODO**
- [ ] Add `bot/whatsapp_bot.py` — a thin adapter like the Telegram one
- [ ] Choose provider: **Twilio WhatsApp** (easiest) or **Meta WhatsApp Cloud API**
- [ ] Map WhatsApp phone number → `session_id` (per-user memory, same as chat_id)
- [ ] Point it at the **same `/chat` API** (no brain changes needed)
- [ ] Add its container to `docker-compose.prod.yml`

**Suggestions / how**
- 🎯 This is where our architecture pays off: because the **brain is the API**
  and the bot is just a thin adapter, adding WhatsApp = **one new file that calls
  the same `/chat`**. Telegram, WhatsApp, a web widget, Instagram — all reuse the
  same agent + memory + tools.
- WhatsApp needs a **public HTTPS webhook** (unlike Telegram polling), so this is
  the point where you'd add Nginx + TLS (or use Twilio's hosted webhook).
- Twilio's WhatsApp **sandbox** is the fastest way to prototype (no Meta business
  verification).

```
        ┌── Telegram bot ──┐
        ├── WhatsApp bot ──┤──►  /chat API  ──►  Agent + Tools + Memory
        └── Web widget ────┘        (one shared brain)
```

---

## Epic 5 — My additional suggestions (future)

**Scale & cost**
- [ ] **Semantic cache** (Redis) — cache answers to repeated/similar questions;
      big cost + latency savings when questions cluster.
- [ ] Migrate stores to **managed services** as traffic grows (Cloud SQL,
      Memorystore, Qdrant Cloud) and the app to Cloud Run — only when a single VM
      is no longer enough.
- [ ] **Autoscaling** for the API once traffic is real.

**Safety & trust**
- [ ] **Guardrails / moderation** on inputs & outputs (important once public).
- [ ] **PII redaction** in logs; privacy policy if handling customer data.
- [ ] Stronger `POSTGRES_PASSWORD` + secrets in a vault.

**Product**
- [ ] **Product images** — customer sends a photo → CLIP matches it to the catalog
      (ties into your CV roadmap, Month 2).
- [ ] **Real catalog** + an `ingredients`/allergens column; live inventory sync.
- [ ] **Order flow** — "add to cart / place order" (adds transactional SQL).
- [ ] **Multilingual** — Hinglish/Hindi support (embeddings + LLM already handle
      it fairly well; add eval coverage).
- [ ] **A/B test prompts** — compare system-prompt variants on the eval set.

---

## Suggested order (value / effort)

1. **Observability (Epic 2)** — you can't improve what you can't see. Start with
   LangSmith + a conversations table. *Low effort, unlocks everything else.*
2. **CI/CD (Epic 1)** — stop manual deploys once you're iterating often.
3. **Quality loop (Epic 3)** — prompt/RAG fixes + an eval set (fine-tune later).
4. **WhatsApp (Epic 4)** — add a channel once the brain is solid.
5. **Scale/safety/product (Epic 5)** — as real usage grows.

> Principle: **measure → improve prompts/RAG → automate → add channels → scale.**
> Fine-tuning and managed-infra come last, only when simpler wins are exhausted.
