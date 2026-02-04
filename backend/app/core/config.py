"""
Application configuration using Pydantic settings.
Loads environment variables and provides typed configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

# Load .env file explicitly using python-dotenv
# This ensures .env is loaded regardless of where the code runs from
from dotenv import load_dotenv
from enum import Enum

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MSSQL = "mssql"
    ORACLE = "oracle"

# Find .env file - check multiple possible locations
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # backend/.env
    Path(__file__).parent.parent.parent.parent / ".env",  # root/.env
    Path.cwd() / ".env",  # Current working directory
    Path.home() / ".env",  # Home directory (fallback)
]

# Load the first .env file found
env_loaded = False
loaded_path = None
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        loaded_path = env_path
        break

# If no .env file found, try loading from default location (current directory)
if not env_loaded:
    load_dotenv(override=True)
    loaded_path = "current directory (default)"

# Log which .env file was loaded (but don't log sensitive values)
# Use try-except to avoid issues if loguru isn't available yet
try:
    from loguru import logger
    if env_loaded or os.getenv("GROQ_API_KEY"):
        logger.info(f"Environment variables loaded from: {loaded_path}")
        # Check if GROQ_API_KEY is set (without logging the actual key)
        if os.getenv("GROQ_API_KEY"):
            key_length = len(os.getenv("GROQ_API_KEY", ""))
            logger.info(f"GROQ_API_KEY is set (length: {key_length} characters)")
        else:
            logger.warning("GROQ_API_KEY is not set in environment variables")
except ImportError:
    # Loguru not available yet, skip logging
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings - Support multiple database types
    DATABASE_TYPE: DatabaseType = DatabaseType.POSTGRESQL  # Options: postgresql, mysql, sqlite, mssql, oracle
    DATABASE_URL: Optional[str] = None  # Override connection string if provided
    
    # PostgreSQL settings (default)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_bi_db"
    
    # MySQL settings
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "ai_bi_db"
    
    # SQLite settings
    SQLITE_PATH: str = "ai_bi.db"
    
    # Database schema (for multi-schema databases)
    DATABASE_SCHEMA: str = "public"  # public for PostgreSQL, database name for MySQL
    
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
        """Construct database connection URL based on DATABASE_TYPE."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        db_type = self.DATABASE_TYPE.lower()
        
        if db_type in ["postgresql", "postgres"]:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif db_type in ["mysql", "mariadb"]:
            return (
                f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            )
        elif db_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    class Config:
        # env_file is handled by explicit load_dotenv() above
        # This ensures .env is loaded before Pydantic tries to read it
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables
        env_file_encoding = "utf-8"


settings = Settings()

# Verify GROQ_API_KEY was loaded correctly after Settings initialization
try:
    from loguru import logger
    if settings.GROQ_API_KEY:
        key_length = len(settings.GROQ_API_KEY)
        logger.info(f"Settings loaded: GROQ_API_KEY is set (length: {key_length} characters)")
    else:
        logger.warning("Settings loaded: GROQ_API_KEY is NOT set. Please check your .env file.")
except ImportError:
    pass

