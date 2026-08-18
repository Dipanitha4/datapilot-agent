"""
config.py
Central configuration management for the Travel AI Agent platform.
All environment variables are loaded here via pydantic-settings.
Every other module imports from this file — never use os.getenv() directly.
Secrets have no defaults — they must be set in .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):

    # ─── LLM Configuration ───────────────────────────────────────────────────
    GROQ_API_KEY: str = Field(description="Groq API key — required")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_TPM_LIMIT: int = Field(default=6000)

    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.1")
    USE_OLLAMA_FALLBACK: bool = Field(default=True)

    # ─── PostgreSQL ──────────────────────────────────────────────────────────
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="travel_ai")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(description="PostgreSQL password — required, set in .env")
    DATABASE_URL: str = Field(description="Full PostgreSQL connection URL — set in .env")

    # ─── Redis ───────────────────────────────────────────────────────────────
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_URL: str = Field(default="redis://localhost:6379")  # no password in local Docker

    # ─── LangGraph Checkpointer (2-layer state) ───────────────────────────────
    LANGGRAPH_CHECKPOINT_DB: str = Field(
        description="PostgreSQL URL for LangGraph state checkpointer — set in .env"
    )

    # ─── RAG / PgVector ──────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    RAG_COLLECTION_NAME: str = Field(default="travel_policy_docs")
    RAG_CHUNK_SIZE: int = Field(default=500)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    POLICY_DOCS_DIR: str = Field(default="data/policy_documents")

    # ─── LangSmith Monitoring ─────────────────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = Field(default=False)
    LANGCHAIN_API_KEY: str = Field(default="")
    LANGCHAIN_PROJECT: str = Field(default="travel-ai-agent")

    # ─── Observability ────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4317")
    OTEL_SERVICE_NAME: str = Field(default="travel-ai-agent")

    # ─── API ──────────────────────────────────────────────────────────────────
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_SECRET_KEY: str = Field(description="API secret key — set in .env")

    # ─── Business Rules ───────────────────────────────────────────────────────
    APPROVAL_THRESHOLD_USD: float = Field(default=500.0)
    LOYALTY_POINTS_PER_USD: float = Field(default=1.0)
    POINTS_TO_USD_RATE: float = Field(default=0.25)
    MAX_CONVERSATION_HISTORY: int = Field(default=10)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()