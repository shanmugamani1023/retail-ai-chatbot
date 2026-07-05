"""Agent tools — Phase 1.

Two tools the agent can call. The docstrings are critical: the tool-calling
agent reads them to decide which tool to use. Good docstrings ARE the router.

  - search_products     : semantic search over descriptions (RAG / Qdrant)
  - query_inventory_sql : exact facts via read-only SQL (Postgres)

Connections are created lazily and cached (module-level singletons) so we
don't reconnect on every call.
"""
from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from langchain_qdrant import QdrantVectorStore

from src.config import settings
from src.ingest import get_embeddings

# --- lazy singletons -------------------------------------------------------
_vectorstore = None
_engine = None


def _get_vectorstore() -> QdrantVectorStore:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=get_embeddings(),
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
        )
    return _vectorstore


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.postgres_url)
    return _engine


# --- tools -----------------------------------------------------------------
@tool
def search_products(query: str) -> str:
    """Search product DESCRIPTIONS for recommendations or features.

    Use this for descriptive / semantic questions, such as:
    'is X good for dry hair', 'recommend a soda', 'tell me about X',
    'what helps with dandruff', or any question about product qualities.

    Input: a natural-language description of what the customer wants.
    """
    docs = _get_vectorstore().similarity_search(query, k=settings.top_k)
    if not docs:
        return "No matching products found."
    lines = []
    for d in docs:
        m = d.metadata
        lines.append(
            f"- {m['name']} ({m['brand']}, {m['category']}) "
            f"- Rs.{m['price']:.0f}, stock: {m['stock']} {m['unit']}. "
            f"{d.page_content.split('. ', 1)[-1]}"
        )
    return "\n".join(lines)


@tool
def query_inventory_sql(sql_query: str) -> str:
    """Run a read-only SQL SELECT for EXACT counts, prices, or stock.

    Use this for numeric / exact questions: how many, total stock, cheapest,
    most expensive, price of X, items under/over a price, counts by category.

    Input: a valid PostgreSQL SELECT statement against this table:

      products(
        id INTEGER, name TEXT, category TEXT, brand TEXT,
        price NUMERIC, stock INTEGER, unit TEXT, description TEXT
      )

    Valid categories (exact values):
      'Beverages', 'Snacks', 'Personal Care', 'Household',
      'Staples', 'Dairy', 'Instant Food'.

    Matching tips (IMPORTANT for correct results):
    - Use case-insensitive fuzzy matching: name ILIKE '%keyword%'.
    - For a brand/product family, match the keyword only, e.g.
      HP products -> name ILIKE '%HP%'; Pepsi -> name ILIKE '%pepsi%'.
    - Sodas/colas/soft drinks/juice/water are category 'Beverages'
      (there is no 'soda' category). For concept words, also try
      (name ILIKE '%x%' OR description ILIKE '%x%').
    - "in stock" means stock > 0.

    Examples:
      SELECT COUNT(*) FROM products WHERE name ILIKE '%HP%' AND name ILIKE '%shampoo%';
      SELECT name, price FROM products WHERE category='Beverages' AND stock>0 ORDER BY price LIMIT 1;
    Only SELECT statements are allowed.
    """
    q = sql_query.strip().rstrip(";")
    if not q.lower().startswith("select"):
        return "Only SELECT statements are allowed."
    try:
        with _get_engine().connect() as conn:
            result = conn.execute(text(q))
            cols = list(result.keys())
            rows = result.fetchall()
    except Exception as exc:  # surface the error so the agent can retry/rephrase
        return f"SQL error: {exc}"
    if not rows:
        return "No rows matched."
    header = " | ".join(cols)
    body = "\n".join(" | ".join(str(v) for v in row) for row in rows)
    return f"{header}\n{body}"


TOOLS = [search_products, query_inventory_sql]
