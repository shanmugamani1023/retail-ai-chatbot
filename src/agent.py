"""Tool-calling agent + memory — Phase 2.

Builds a LangChain tool-calling agent over the tools in src/tools.py,
wrapped with per-user (chat_id) conversation memory backed by Redis.
"""
from src.config import settings
from src.tools import TOOLS


def get_agent():
    """Return the tool-calling agent executor (with Redis-backed memory)."""
    raise NotImplementedError("Phase 2: build tool-calling agent")


def answer(message: str, session_id: str) -> str:
    """Run the agent for one turn: load memory -> agent -> save memory."""
    raise NotImplementedError("Phase 2: wire memory + agent")
