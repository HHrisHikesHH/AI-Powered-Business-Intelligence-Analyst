"""
Application configuration using Pydantic settings.
Loads environment variables and provides typed configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_bi_db"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    
    # Groq API settings
    GROQ_API_KEY: Optional[str] = None
    
    # LLM Model Configuration
    # Available models: llama-3.1-8b-instant, llama-3.3-70b-versatile, 
    # openai/gpt-oss-20b, openai/gpt-oss-120b, qwen/qwen3-32b, etc.
    LLM_MODEL_SIMPLE: str = "llama-3.1-8b-instant"  # Fast, cost-effective for simple queries
    LLM_MODEL_MEDIUM: str = "llama-3.3-70b-versatile"  # Balanced for medium complexity
    LLM_MODEL_COMPLEX: str = "openai/gpt-oss-120b"  # Powerful for complex queries
    LLM_MODEL_DEFAULT: str = "llama-3.3-70b-versatile"  # Default model
    
    # Application settings
    ENVIRONMENT: str = "development"
    BACKEND_PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    
    # Performance settings
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    EMBEDDING_BATCH_SIZE: int = 50
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()

