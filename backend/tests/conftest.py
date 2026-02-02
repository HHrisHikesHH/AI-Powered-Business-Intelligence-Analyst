"""
Pytest configuration and fixtures.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
async def test_db():
    """Create a test database session (requires actual database)."""
    engine = create_async_engine(
        settings.database_url.replace("/ai_bi_db", "/test_db"),
        echo=False
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

