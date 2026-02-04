"""
Database connection and session management.
Uses modular database adapter system to support multiple database types.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from app.core.config import settings
from app.core.database_adapter import create_database_adapter, DatabaseAdapter

# Global database adapter instance
_db_adapter: DatabaseAdapter = None

# Base class for models
Base = declarative_base()


def get_db_adapter() -> DatabaseAdapter:
    """Get or create database adapter instance."""
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = create_database_adapter(
            db_type=settings.DATABASE_TYPE,
            connection_string=settings.database_url
        )
        logger.info(f"Database adapter created for type: {settings.DATABASE_TYPE}")
    return _db_adapter


def get_session_factory() -> async_sessionmaker:
    """Get async session factory from database adapter."""
    adapter = get_db_adapter()
    return adapter.get_session_factory()


# Lazy initialization - will be created on first use
AsyncSessionLocal = None

def _ensure_session_factory():
    """Ensure session factory is initialized."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = get_session_factory()
    return AsyncSessionLocal


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session.
    Used in FastAPI route handlers.
    """
    factory = _ensure_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database connection and verify connectivity."""
    try:
        adapter = get_db_adapter()
        is_connected = await adapter.test_connection()
        if is_connected:
            logger.info(f"Database connection established successfully ({settings.DATABASE_TYPE})")
        else:
            raise ConnectionError("Database connection test failed")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

