"""
Pytest configuration and fixtures.
"""
import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
# Tests create their own adapters with session factories


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session



