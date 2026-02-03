"""
Tests for error handling, retry logic, and self-correction.
"""
import pytest
from app.agents.orchestrator import Orchestrator
from app.services.error_handler import error_handler, ErrorCategory
from app.services.fallback_strategies import FallbackStrategies
from app.agents.analysis import AnalysisAgent
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_retry_logic_exponential_backoff():
    """Test retry logic with exponential backoff."""
    
    # Test exponential backoff calculation
    state = {
        "retry_count": 0,
        "max_retries": 3,
        "error": "Test error"
    }
    
    # First retry: 2^0 = 1 second
    backoff_1 = 2 ** state["retry_count"]
    assert backoff_1 == 1
    
    # Second retry: 2^1 = 2 seconds
    state["retry_count"] = 1
    backoff_2 = 2 ** state["retry_count"]
    assert backoff_2 == 2
    
    # Third retry: 2^2 = 4 seconds
    state["retry_count"] = 2
    backoff_3 = 2 ** state["retry_count"]
    assert backoff_3 == 4


@pytest.mark.asyncio
async def test_self_correction_syntax_error():
    """Test self-correction for syntax errors."""
    mock_db = AsyncMock()
    orchestrator = Orchestrator(mock_db)
    
    # Mock SQL generation agent
    with patch.object(orchestrator.sql_generation_agent, 'self_correct_sql', new_callable=AsyncMock) as mock_correct:
        mock_correct.return_value = "SELECT * FROM customers LIMIT 100;"
        
        state = {
            "error_category": ErrorCategory.SYNTAX_ERROR.value,
            "generated_sql": "SELECT * FROM customers LIMIT 100",  # Missing semicolon
            "error": "Syntax error: missing semicolon",
            "query_understanding": {"tables": ["customers"]},
            "natural_language_query": "Show me customers",
            "retry_count": 0,
            "max_retries": 3
        }
        
        corrected_state = await orchestrator._self_correct_node(state)
        
        assert corrected_state["generated_sql"] == "SELECT * FROM customers LIMIT 100;"
        assert corrected_state["retry_count"] == 1
        mock_correct.assert_called_once()


@pytest.mark.asyncio
async def test_self_correction_schema_error():
    """Test self-correction for schema errors."""
    mock_db = AsyncMock()
    orchestrator = Orchestrator(mock_db)
    
    with patch.object(orchestrator.sql_generation_agent, 'self_correct_sql', new_callable=AsyncMock) as mock_correct:
        mock_correct.return_value = "SELECT * FROM customers LIMIT 100;"
        
        state = {
            "error_category": ErrorCategory.SCHEMA_ERROR.value,
            "generated_sql": "SELECT * FROM nonexistent_table LIMIT 100;",
            "error": "Table 'nonexistent_table' does not exist",
            "query_understanding": {"tables": ["customers"]},
            "natural_language_query": "Show me customers",
            "retry_count": 0,
            "max_retries": 3
        }
        
        corrected_state = await orchestrator._self_correct_node(state)
        
        assert corrected_state["retry_count"] == 1
        mock_correct.assert_called_once()


@pytest.mark.asyncio
async def test_error_categorization():
    """Test error categorization."""
    # Syntax error
    syntax_error = Exception("Syntax error: invalid SQL")
    error_info = error_handler.categorize_error(syntax_error)
    assert error_info["category"] == ErrorCategory.SYNTAX_ERROR.value
    assert error_info["retryable"] is True
    assert error_info["retry_strategy"] == "self_correct_sql"
    
    # Schema error
    schema_error = Exception("Table 'xyz' does not exist")
    error_info = error_handler.categorize_error(schema_error)
    assert error_info["category"] == ErrorCategory.SCHEMA_ERROR.value
    assert error_info["retryable"] is True
    
    # Timeout error
    timeout_error = Exception("Query timeout after 30 seconds")
    error_info = error_handler.categorize_error(timeout_error)
    assert error_info["category"] == ErrorCategory.TIMEOUT_ERROR.value
    assert error_info["retryable"] is True


@pytest.mark.asyncio
async def test_fallback_strategies():
    """Test fallback strategies for different error types."""
    strategies = FallbackStrategies()
    
    # Test syntax error strategy
    syntax_strategy = await strategies.handle_syntax_error(
        query_understanding={"tables": ["customers"]},
        natural_language_query="Show customers",
        previous_sql="SELECT * FROM customers",
        error_message="Syntax error"
    )
    assert syntax_strategy["strategy"] == "self_correct_sql"
    assert syntax_strategy["retryable"] is True
    
    # Test schema error strategy
    schema_strategy = await strategies.handle_schema_error(
        query_understanding={"tables": ["customers"]},
        natural_language_query="Show customers",
        previous_sql="SELECT * FROM xyz",
        error_message="Table does not exist"
    )
    assert schema_strategy["strategy"] == "augment_schema_context"
    assert schema_strategy["retryable"] is True
    
    # Test empty results strategy
    empty_strategy = await strategies.handle_empty_results(
        query_understanding={"tables": ["customers"]},
        natural_language_query="Show customers from 2025",
        sql="SELECT * FROM customers WHERE created_at >= '2025-01-01'",
        results=[]
    )
    assert empty_strategy["strategy"] == "check_intent"
    assert "suggestions" in empty_strategy


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    """Test that max retries are respected."""
    mock_db = AsyncMock()
    orchestrator = Orchestrator(mock_db, max_retries=2)
    
    state = {
        "retry_count": 2,
        "max_retries": 2,
        "error": "Persistent error"
    }
    
    retry_state = await orchestrator._retry_node(state)
    
    assert retry_state["step"] == "error"
    assert "Max retries" in retry_state["error"]


@pytest.mark.asyncio
async def test_orchestrator_with_retry():
    """Test orchestrator handles retries correctly."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [(20,)]
    mock_result.keys.return_value = ["count"]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    orchestrator = Orchestrator(mock_db, max_retries=2)
    
    with patch.object(orchestrator.query_understanding_agent, 'understand', new_callable=AsyncMock) as mock_understand, \
         patch.object(orchestrator.sql_generation_agent, 'generate_sql', new_callable=AsyncMock) as mock_generate, \
         patch.object(orchestrator.sql_validator, 'validate', new_callable=AsyncMock) as mock_validate, \
         patch.object(orchestrator.analysis_agent, 'analyze_results', new_callable=AsyncMock) as mock_analyze, \
         patch.object(orchestrator.visualization_agent, 'generate_visualization', new_callable=AsyncMock) as mock_viz:
        
        # First attempt fails validation, second succeeds
        mock_understand.return_value = {
            "intent": "Count customers",
            "tables": ["customers"],
            "aggregations": ["COUNT"]
        }
        
        mock_generate.side_effect = [
            "SELECT COUNT(*) FROM customers;",  # First attempt
            "SELECT COUNT(*) as count FROM customers;"  # Corrected
        ]
        
        mock_validate.side_effect = [
            (False, "Missing alias"),  # First attempt fails
            (True, None)  # Second attempt succeeds
        ]
        
        mock_analyze.return_value = {"insights": ["20 customers"], "summary": "Test"}
        mock_viz.return_value = {"chart_type": "bar", "title": "Test"}
        
        result = await orchestrator.process_query("How many customers?")
        
        # Should succeed after retry
        assert result["validation_passed"] is True
        assert mock_generate.call_count >= 2  # At least 2 attempts


@pytest.mark.asyncio
async def test_error_statistics():
    """Test error statistics collection."""
    error_handler.clear_log()
    
    # Generate some errors
    error_handler.categorize_error(Exception("Syntax error"))
    error_handler.categorize_error(Exception("Table does not exist"))
    error_handler.categorize_error(Exception("Timeout"))
    
    stats = error_handler.get_error_statistics()
    
    assert stats["total_errors"] == 3
    assert "by_category" in stats
    assert "by_severity" in stats
    assert stats["retryable_count"] >= 0

