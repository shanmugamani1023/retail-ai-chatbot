"""LLM client — Phase 2.

Groq chat model with retry + fallback so one flaky API call doesn't
become a failed customer reply.
"""
from src.config import settings


def get_llm():
    """Return a configured Groq chat model (with retry/fallback in Phase 2)."""
    raise NotImplementedError("Phase 2: build Groq client")
