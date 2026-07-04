"""FastAPI backend.

Endpoints:
  GET  /health          liveness  (is the app up?)
  GET  /ready           readiness (are the data stores reachable?)
  POST /chat            main endpoint: message + session_id -> answer
  POST /upload-catalog  re-ingest the catalog

Run (dev):  uvicorn api.main:app --reload   (or: python -m api.main)
"""
from fastapi import FastAPI
from pydantic import BaseModel

from src.config import settings

app = FastAPI(title="Retail AI Chatbot API", version="0.1.0")


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health():
    """Liveness — the app is running."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness — data stores reachable. (Full checks land in Phase 2.)"""
    return {
        "status": "ok",
        "stores": {"redis": "unchecked", "postgres": "unchecked", "qdrant": "unchecked"},
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Main endpoint. Phase 2 routes this through the tool-calling agent."""
    # TODO(Phase 2): from src.agent import answer; return answer(req.message, req.session_id)
    return ChatResponse(answer="(not implemented yet — Phase 2 wires the agent)")


@app.post("/upload-catalog")
def upload_catalog():
    """Re-ingest the catalog into Qdrant + Postgres. (Phase 1/2)."""
    # TODO(Phase 1/2): from src.ingest import build_index; build_index()
    return {"status": "not implemented yet"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
