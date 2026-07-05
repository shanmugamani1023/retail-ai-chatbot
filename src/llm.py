"""LLM client — Phase 2.

Groq chat model with timeout + retry. A smaller fallback model id is exposed
so the agent layer can retry on a different model if the primary hard-fails.
"""
from langchain_groq import ChatGroq

from src.config import settings

# Larger model used as a fallback if the primary hard-fails.
FALLBACK_MODEL = "openai/gpt-oss-120b"


def get_llm(model: str | None = None) -> ChatGroq:
    """Return a configured Groq chat model.

    - timeout: don't hang forever on a slow call.
    - max_retries: ride out transient errors with backoff.
    """
    return ChatGroq(
        model=model or settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=settings.llm_temperature,
        timeout=30,
        max_retries=2,
    )
