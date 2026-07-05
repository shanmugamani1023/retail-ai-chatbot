"""Tool-calling agent + memory — Phase 2.

Builds a LangChain (v1) tool-calling agent over the tools in src/tools.py.
The agent (Groq LLM) decides which tool to call — there is no hand-written
router. Per-user conversation memory is stored in Redis, keyed by session_id
(the Telegram chat_id), so the bot is multi-turn.
"""
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_community.chat_message_histories import RedisChatMessageHistory

from src.config import settings
from src.llm import FALLBACK_MODEL, get_llm
from src.tools import TOOLS

SYSTEM_PROMPT = """You are a warm, helpful shopping assistant for a retail store.
Answer customer questions about products using your tools:

- search_products: for descriptions, features, or recommendations
  (e.g. "good for dry hair", "recommend a soda", "tell me about X").
- query_inventory_sql: for EXACT numbers — counts, stock, or prices
  (write a PostgreSQL SELECT against the products table).

Rules:
- Always use a tool to get facts. Never invent products, prices, or stock.
- Use query_inventory_sql for "how many / cheapest / price / in stock".
- Use search_products for recommendations or descriptive questions.
- You may use BOTH tools when needed (e.g. "cheapest dandruff shampoo").
- Prices are in Indian Rupees (Rs.). Keep replies short, friendly, and clear.
- If nothing matches, say so honestly.
- Reply in plain text suitable for a chat app (Telegram). Do NOT use markdown
  tables or headings; use short sentences or simple dash bullets. Keep it concise.
"""

# Primary agent (built once at import). It's a compiled LangGraph graph:
# input  -> {"messages": [...]}, output -> {"messages": [...]}.
_agent = create_agent(get_llm(), TOOLS, system_prompt=SYSTEM_PROMPT)


def _history(session_id: str) -> RedisChatMessageHistory:
    """Per-session chat history in Redis (auto-expires after the TTL)."""
    return RedisChatMessageHistory(
        session_id=session_id,
        url=settings.redis_url,
        ttl=settings.session_ttl_seconds,
    )


def _run(agent, message: str, past_messages) -> str:
    """Invoke the agent with prior turns + the new message; return the reply."""
    result = agent.invoke({"messages": past_messages + [HumanMessage(content=message)]})
    return result["messages"][-1].content


def answer(message: str, session_id: str) -> str:
    """Run one turn: load memory -> agent picks tools -> save memory.

    On a hard failure of the primary model, retry once on the fallback model.
    """
    history = _history(session_id)
    past = history.messages  # prior human/AI turns for this session
    try:
        reply = _run(_agent, message, past)
    except Exception:
        fallback_agent = create_agent(get_llm(FALLBACK_MODEL), TOOLS, system_prompt=SYSTEM_PROMPT)
        reply = _run(fallback_agent, message, past)

    history.add_user_message(message)
    history.add_ai_message(reply)
    return reply
