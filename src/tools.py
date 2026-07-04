"""Agent tools — Phase 1.

The docstrings below are critical: the tool-calling agent reads them to
decide which tool to use. Good docstrings ARE the router.
"""
from langchain_core.tools import tool


@tool
def query_inventory_sql(query: str) -> str:
    """Get EXACT counts, stock levels, or prices from the inventory database.

    Use this for questions about numbers, such as:
    how many, total stock, quantity available, cheapest, most expensive,
    price of X, or items under/over a given price.
    """
    raise NotImplementedError("Phase 1: implement SQL tool")


@tool
def search_products(query: str) -> str:
    """Search product DESCRIPTIONS for recommendations or features.

    Use this for descriptive / semantic questions, such as:
    'is X good for dry hair', 'recommend a soda', 'tell me about X',
    'what products help with dandruff', or any question about qualities.
    """
    raise NotImplementedError("Phase 1: implement RAG tool")


TOOLS = [query_inventory_sql, search_products]
