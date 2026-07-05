"""Simple per-session rate limiting — Phase 2.

A fixed-window counter in Redis: at most RATE_LIMIT messages per WINDOW seconds
per session_id. Protects against abuse and runaway LLM cost.
"""
import redis

from src.config import settings

RATE_LIMIT = 20   # messages
WINDOW = 60       # seconds

_client = None


def _redis():
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url)
    return _client


def allow(session_id: str) -> bool:
    """Return True if this session is under the limit, else False."""
    key = f"ratelimit:{session_id}"
    count = _redis().incr(key)
    if count == 1:
        _redis().expire(key, WINDOW)
    return count <= RATE_LIMIT
