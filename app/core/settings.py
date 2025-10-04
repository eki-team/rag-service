"""
NASA Biology RAG - Settings
Configuración centralizada para el servicio RAG de biología espacial.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Settings para NASA RAG - Vector store + OpenAI"""
    
    # === OpenAI Config ===
    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.2
    
    # === Vector Backend ===
    VECTOR_BACKEND: Literal["mongodb", "pgvector"] = "mongodb"
    
    # === MongoDB (opción A - prod) ===
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "nasa_bio"
    MONGODB_COLLECTION: str = "pub_chunks"
    MONGODB_VECTOR_INDEX: str = "vector_index"  # nombre del índice vectorial
    
    # === PostgreSQL + pgvector (opción B - comentada) ===
    # POSTGRES_USER: str = ""
    # POSTGRES_PASSWORD: str = ""
    # POSTGRES_DB: str = "nasa_rag"
    # DB_HOST: str = "localhost"
    # DB_PORT: str = "5432"
    
    # === NASA Config ===
    NASA_MODE: bool = True
    NASA_ALLOWED_SOURCES: str = "OSDR,LSL,TASKBOOK"
    NASA_GUIDED_ENABLED: bool = False  # feature flag para modo Guided
    NASA_DEFAULT_ORG: str = "nasa"
    
    # === Retrieval Config ===
    DEFAULT_TOP_K: int = 8
    MAX_TOP_K: int = 20
    MIN_SIMILARITY: float = 0.70
    ENABLE_RERANK: bool = False  # re-rank con LLM (opcional)
    
    # === Rate Limiting (opcional) ===
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: int = 60  # segundos
    
    # === CORS ===
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # === Logging ===
    LOG_LEVEL: str = "INFO"
    LOG_RETRIEVAL: bool = True
    LOG_GROUNDING: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    @property
    def allowed_sources_list(self) -> list[str]:
        """Parse allowed sources"""
        return [s.strip().upper() for s in self.NASA_ALLOWED_SOURCES.split(",") if s.strip()]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins"""
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
