"""Ingestion — Phase 1.

Loads data/products.csv into TWO stores:
  - PostgreSQL : structured rows      (for exact SQL queries)
  - Qdrant     : embedded descriptions (for semantic search / RAG)

We keep ONE document per product (descriptions are short), so each vector
carries the product's metadata (price, stock, ...) alongside its meaning.

Run:  python -m src.ingest
"""
import pandas as pd
from sqlalchemy import create_engine
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

from src.config import settings

CSV_PATH = "data/products.csv"
TABLE_NAME = "products"


def _load_df() -> pd.DataFrame:
    """Read the catalog CSV into a DataFrame."""
    return pd.read_csv(CSV_PATH)


def _to_postgres(df: pd.DataFrame) -> int:
    """Write the structured rows into PostgreSQL (replace on re-ingest)."""
    engine = create_engine(settings.postgres_url)
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    engine.dispose()
    return len(df)


def get_embeddings() -> HuggingFaceEmbeddings:
    """all-MiniLM embedding model (local, normalized vectors)."""
    return HuggingFaceEmbeddings(
        model_name=settings.embed_model,
        encode_kwargs={"normalize_embeddings": True},
    )


def _row_to_document(row: pd.Series) -> Document:
    """One product -> one Document (text for meaning, metadata for facts)."""
    content = (
        f"{row['name']} by {row['brand']} ({row['category']}). "
        f"{row['description']}"
    )
    metadata = {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "category": str(row["category"]),
        "brand": str(row["brand"]),
        "price": float(row["price"]),
        "stock": int(row["stock"]),
        "unit": str(row["unit"]),
    }
    return Document(page_content=content, metadata=metadata)


def _to_qdrant(df: pd.DataFrame) -> int:
    """Embed product descriptions and store them in Qdrant (recreate on re-ingest)."""
    docs = [_row_to_document(r) for _, r in df.iterrows()]
    QdrantVectorStore.from_documents(
        docs,
        embedding=get_embeddings(),
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        force_recreate=True,   # clean slate each ingest (safe for the MVP)
    )
    return len(docs)


def build_index() -> dict:
    """Load CSV -> Postgres (rows) + Qdrant (vectors). Returns counts."""
    df = _load_df()
    n_sql = _to_postgres(df)
    n_vec = _to_qdrant(df)
    return {"postgres_rows": n_sql, "qdrant_vectors": n_vec}


if __name__ == "__main__":
    print("Ingesting catalog...")
    result = build_index()
    print(
        f"Done. Postgres rows: {result['postgres_rows']}, "
        f"Qdrant vectors: {result['qdrant_vectors']}."
    )
