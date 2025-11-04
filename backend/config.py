"""
Configuration management for Swiss Voting Assistant
Loads settings from environment variables with defaults
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    # Swisscom Apertus API (Swiss AI Platform)
    SWISS_AI_PLATFORM_API_KEY: str = ""  # Primary key (from hacker profile)
    APERTUS_API_KEY: str = ""  # Alternative name
    APERTUS_API_URL: str = "https://api.swisscom.com/apertus/v1"
    APERTUS_MODEL: str = "Apertus-70B-Instruct-2509"
    APERTUS_RATE_LIMIT_RPM: int = 300  # 5 requests per second = 300/min
    APERTUS_RATE_LIMIT_TPM: int = 100000  # 100k tokens per minute

    # Database
    DATABASE_URL: str = "postgresql://swiss_voting:dev_password@postgres:5432/swiss_voting_db"

    # ChromaDB
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "swiss_voting_brochures"

    # Embedding Model
    EMBEDDING_MODEL: str = "paraphrase-multilingual-mpnet-base-v2"

    # RAG Settings
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.7
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Application Settings
    API_VERSION: str = "1.0.0"
    MAX_QUERY_LENGTH: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Initialize settings (singleton pattern)
settings = Settings()


def get_database_url() -> str:
    """Get database URL for SQLAlchemy"""
    return settings.DATABASE_URL


def get_chromadb_url() -> str:
    """Get ChromaDB connection URL"""
    return f"http://{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}"


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.ENVIRONMENT.lower() == "development"


def get_apertus_api_key() -> str:
    """Get Apertus API key (try both environment variable names)"""
    return settings.SWISS_AI_PLATFORM_API_KEY or settings.APERTUS_API_KEY
