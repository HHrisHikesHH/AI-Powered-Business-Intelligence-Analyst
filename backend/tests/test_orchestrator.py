"""
Integration tests for orchestrator.
"""
import pytest
from app.agents.orchestrator import Orchestrator
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_orchestrator_simple_query():
    """Test orchestrator with a simple query."""
    # Mock database session
    mock_db = AsyncMock()
    mock_result = MagicMock()
    # SQLAlchemy returns Row objects (tuple-like), not dictionaries
    # fetchall() returns list of tuples, keys() returns column names
    mock_result.fetchall.return_value = [(20,)]  # Tuple with one value
    mock_result.keys.return_value = ["count"]  # Column names
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Mock schema validation
    with patch('app.agents.sql_validator.SQLValidator.validate', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        
        orchestrator = Orchestrator(mock_db)
        
        # Mock agents
        with patch.object(orchestrator.query_understanding_agent, 'understand', new_callable=AsyncMock) as mock_understand, \
             patch.object(orchestrator.sql_generation_agent, 'generate_sql', new_callable=AsyncMock) as mock_generate:
            
            mock_understand.return_value = {
                "intent": "Count customers",
                "tables": ["customers"],
                "columns": ["id"],
                "filters": [],
                "aggregations": ["COUNT"],
                "group_by": [],
                "order_by": None,
                "limit": None,
                "ambiguities": [],
                "needs_clarification": False
            }
            
            mock_generate.return_value = "SELECT COUNT(*) as count FROM customers;"
            
            result = await orchestrator.process_query("How many customers do we have?")
            
            assert result["sql"] == "SELECT COUNT(*) as count FROM customers;"
            assert result["validation_passed"] is True
            assert len(result["results"]) == 1
            assert result["results"][0]["count"] == 20

