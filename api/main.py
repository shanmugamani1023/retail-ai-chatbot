"""FastAPI backend.

Endpoints:
  GET  /health          liveness  (is the app up?)
  GET  /ready           readiness (are the data stores reachable?)
  POST /chat            main endpoint: message + session_id -> answer
  POST /upload-catalog  re-ingest the catalog

Run (dev):  uvicorn api.main:app --reload   (or: python -m api.main)
"""
import httpx
import redis
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from src.config import settings

app = FastAPI(title="Retail AI Chatbot API", version="0.2.0")


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health():
    """Liveness — the app is running."""
    return {"status": "ok"}


def _check_redis() -> str:
    try:
        redis.from_url(settings.redis_url).ping()
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def _check_postgres() -> str:
    try:
        engine = create_engine(settings.postgres_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def _check_qdrant() -> str:
    try:
        httpx.get(f"{settings.qdrant_url}/healthz", timeout=3).raise_for_status()
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


@app.get("/ready")
def ready():
    """Readiness — check every data store is reachable."""
    stores = {
        "redis": _check_redis(),
        "postgres": _check_postgres(),
        "qdrant": _check_qdrant(),
    }
    all_ok = all(v == "ok" for v in stores.values())
    return {"status": "ok" if all_ok else "degraded", "stores": stores}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Main endpoint — routes the message through the tool-calling agent."""
    # imported lazily so the app can start even if the agent deps are slow to load
    from src.agent import answer
    from src.ratelimit import allow

    if not allow(req.session_id):
        return ChatResponse(answer="You're sending messages too fast — please wait a moment. 🙏")
    return ChatResponse(answer=answer(req.message, req.session_id))


@app.post("/upload-catalog")
def upload_catalog():
    """Re-ingest the catalog into Qdrant + Postgres."""
    from src.ingest import build_index

    result = build_index()
    return {"status": "ok", **result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
