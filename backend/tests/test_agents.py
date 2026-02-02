"""
Unit tests for agents.
"""
import pytest
from app.agents.query_understanding import QueryUnderstandingAgent
from app.agents.sql_generation import SQLGenerationAgent
from app.agents.sql_validator import SQLValidator
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_query_understanding_agent():
    """Test Query Understanding Agent."""
    agent = QueryUnderstandingAgent()
    
    # Mock LLM response
    with patch.object(agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '''{
            "intent": "Count total number of customers",
            "tables": ["customers"],
            "columns": ["id"],
            "filters": [],
            "aggregations": ["COUNT"],
            "group_by": [],
            "order_by": null,
            "limit": null,
            "ambiguities": [],
            "needs_clarification": false
        }'''
        
        result = await agent.understand("How many customers do we have?")
        
        assert result["intent"] == "Count total number of customers"
        assert "customers" in result["tables"]
        assert "COUNT" in result["aggregations"]


@pytest.mark.asyncio
async def test_sql_generation_agent():
    """Test SQL Generation Agent."""
    agent = SQLGenerationAgent()
    
    query_understanding = {
        "intent": "Count total number of customers",
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
    
    # Mock LLM and vector store
    with patch.object(agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm, \
         patch.object(agent.vector_store, 'search_similar', new_callable=AsyncMock) as mock_rag:
        
        mock_llm.return_value = "SELECT COUNT(*) as customer_count FROM customers;"
        mock_rag.return_value = []
        
        sql = await agent.generate_sql(query_understanding, "How many customers do we have?")
        
        assert "SELECT" in sql.upper()
        assert "customers" in sql.lower()
        assert "COUNT" in sql.upper()


@pytest.mark.asyncio
async def test_sql_validator():
    """Test SQL Validator."""
    # Mock database session
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("customers", "id"),
        ("customers", "name"),
        ("products", "id"),
        ("products", "name")
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    validator = SQLValidator(mock_db)
    
    # Test valid SQL
    is_valid, error = await validator.validate("SELECT * FROM customers;")
    assert is_valid is True
    assert error is None
    
    # Test invalid SQL (dangerous operation)
    is_valid, error = await validator.validate("DROP TABLE customers;")
    assert is_valid is False
    assert "Dangerous operation" in error
    
    # Test invalid SQL (non-SELECT)
    is_valid, error = await validator.validate("UPDATE customers SET name = 'test';")
    assert is_valid is False
    assert "Only SELECT queries" in error


@pytest.mark.asyncio
async def test_sql_validator_schema_check():
    """Test SQL Validator schema checking."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("customers", "id"),
        ("customers", "name"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    validator = SQLValidator(mock_db)
    await validator._load_schema_cache()
    
    # Test valid table
    is_valid, error = await validator._validate_schema("SELECT * FROM customers;")
    assert is_valid is True
    
    # Test invalid table
    is_valid, error = await validator._validate_schema("SELECT * FROM nonexistent;")
    assert is_valid is False
    assert "does not exist" in error

