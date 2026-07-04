"""Ingestion — Phase 1.

Loads data/products.csv into TWO stores:
  - Qdrant     : embedded product descriptions (for semantic search / RAG)
  - PostgreSQL : structured rows (for exact SQL queries)

Run:  python -m src.ingest
"""
from src.config import settings


def build_index() -> int:
    """Load CSV -> embed descriptions -> Qdrant; load rows -> Postgres.
    Returns number of products ingested.
    """
    raise NotImplementedError("Phase 1: implement ingestion")


if __name__ == "__main__":
    count = build_index()
    print(f"Ingested {count} products into Qdrant + Postgres.")
