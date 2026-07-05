"""Central config. All settings come from environment variables / .env
(12-factor). This is what makes dev->cloud a config change, not a rewrite.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- LLM (Groq) ---
    groq_api_key: str = ""
    llm_model: str = "openai/gpt-oss-20b"   # reliable tool-calling on Groq
    llm_temperature: float = 0.2

    # --- Embeddings (local) ---
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_mode: str = "polling"        # polling (dev) | webhook (prod)
    webhook_url: str = ""

    # --- Data stores ---
    redis_url: str = "redis://localhost:6379/0"
    postgres_url: str = "postgresql+psycopg://retail:retail@localhost:5432/retail"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"

    # --- API ---
    api_url: str = "http://localhost:8000"

    # --- RAG ---
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 4

    # --- Memory ---
    session_ttl_seconds: int = 86400


settings = Settings()
