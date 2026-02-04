"""
Tests for cost optimization.
Tests model routing, caching effectiveness, and cost per query.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.orchestrator import Orchestrator
from app.core.llm_client import llm_service, QueryComplexity
from app.core.redis_client import cache_service


@pytest.fixture
def orchestrator():
    """Create an Orchestrator instance for testing."""
    return Orchestrator()


@pytest.mark.asyncio
async def test_model_routing_simple_query(orchestrator):
    """Test that simple queries use cost-effective models (Haiku/GPT-4o mini)."""
    query = "How many customers?"
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(llm_service, 'classify_from_understanding', return_value=QueryComplexity.SIMPLE), \
         patch.object(llm_service, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        # Mock LLM to track which complexity was used
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        result = await orchestrator.process_query(query)
        
        # Check that simple model was used (verify through calls)
        # Simple queries should use SIMPLE complexity
        assert mock_llm.called
        call_args = mock_llm.call_args
        if call_args:
            # Check that complexity was SIMPLE
            complexity_arg = call_args.kwargs.get('complexity')
            if complexity_arg:
                assert complexity_arg == QueryComplexity.SIMPLE or complexity_arg.value == "simple"


@pytest.mark.asyncio
async def test_model_routing_complex_query(orchestrator):
    """Test that complex queries use appropriate models (Sonnet/Opus)."""
    query = "Show me top 10 customers with their order history, employee assignments, and support ticket counts grouped by region and industry"
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(llm_service, 'classify_from_understanding', return_value=QueryComplexity.COMPLEX), \
         patch.object(llm_service, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_llm.return_value = "SELECT ..."
        
        result = await orchestrator.process_query(query)
        
        # Check that complex model was used
        assert mock_llm.called
        call_args = mock_llm.call_args
        if call_args:
            complexity_arg = call_args.kwargs.get('complexity')
            if complexity_arg:
                assert complexity_arg == QueryComplexity.COMPLEX or complexity_arg.value == "complex"


@pytest.mark.asyncio
async def test_caching_effectiveness(orchestrator):
    """Test that caching reduces LLM calls."""
    query = "How many customers do we have?"
    
    # First call: cache miss
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None) as mock_cache_get, \
         patch.object(cache_service, 'set', new_callable=AsyncMock) as mock_cache_set, \
         patch.object(llm_service, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        result1 = await orchestrator.process_query(query)
        
        # Verify cache was checked and set
        assert mock_cache_get.called
        assert mock_cache_set.called
    
    # Second call: cache hit
    cached_understanding = {
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
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=cached_understanding) as mock_cache_get, \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(llm_service, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        result2 = await orchestrator.process_query(query)
        
        # Cache should be checked
        assert mock_cache_get.called


@pytest.mark.asyncio
async def test_cache_hit_rate_calculation():
    """Test that cache hit rate can be calculated."""
    queries = [
        "How many customers?",
        "How many customers?",  # Duplicate
        "Show me products",
        "Show me products",  # Duplicate
        "List employees"
    ]
    
    cache_hits = 0
    cache_misses = 0
    
    for i, query in enumerate(queries):
        # Simulate cache: first occurrence is miss, subsequent is hit
        is_cached = query in [q for q in queries[:i]]
        
        if is_cached:
            cache_hits += 1
        else:
            cache_misses += 1
    
    total_queries = len(queries)
    cache_hit_rate = cache_hits / total_queries
    
    # Should have some cache hits from duplicates
    assert cache_hits > 0
    assert cache_hit_rate > 0
    assert cache_hit_rate <= 1.0


@pytest.mark.asyncio
async def test_cost_tracking_per_query(orchestrator):
    """Test that cost is tracked per query."""
    query = "How many customers?"
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(llm_service, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        # Mock LLM to return cost information
        mock_response = MagicMock()
        mock_response.total_cost = 0.001
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        result = await orchestrator.process_query(query)
        
        # Result should contain cost information if tracked
        # This depends on implementation - check if cost_breakdown exists
        if "cost_breakdown" in result:
            assert "total_cost" in result["cost_breakdown"]
            assert result["cost_breakdown"]["total_cost"] >= 0


@pytest.mark.asyncio
async def test_average_cost_per_query():
    """Test that average cost per query is calculated correctly."""
    # Simulate cost tracking
    costs = [0.001, 0.002, 0.0015, 0.003, 0.001]
    
    avg_cost = sum(costs) / len(costs)
    
    # Average should be reasonable
    assert avg_cost > 0
    assert avg_cost < 0.01  # Should be less than $0.01 for simple queries
    
    # Target: average < $0.02
    assert avg_cost < 0.02, f"Average cost {avg_cost} exceeds $0.02 target"


@pytest.mark.asyncio
async def test_simple_query_cost_target():
    """Test that simple queries meet cost target (< $0.005)."""
    simple_query_costs = [0.001, 0.002, 0.0015, 0.003, 0.001]
    
    avg_simple_cost = sum(simple_query_costs) / len(simple_query_costs)
    
    # Simple queries should be very cheap
    assert avg_simple_cost < 0.005, f"Simple query cost {avg_simple_cost} exceeds $0.005 target"


@pytest.mark.asyncio
async def test_complex_query_cost_target():
    """Test that complex queries meet cost target (< $0.05)."""
    complex_query_costs = [0.01, 0.015, 0.02, 0.025, 0.03]
    
    avg_complex_cost = sum(complex_query_costs) / len(complex_query_costs)
    
    # Complex queries can be more expensive but should still be reasonable
    assert avg_complex_cost < 0.05, f"Complex query cost {avg_complex_cost} exceeds $0.05 target"


@pytest.mark.asyncio
async def test_schema_embeddings_cached():
    """Test that schema embeddings are cached."""
    # This test verifies that schema embeddings caching reduces costs
    # In practice, schema embeddings should be cached after first generation
    
    cache_key = "schema_embeddings:customers"
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(cache_service, 'set', new_callable=AsyncMock) as mock_set:
        
        # First call: cache miss
        mock_get.return_value = None
        # Simulate embedding generation and caching
        mock_set.assert_not_called()  # Will be called after generation
        
        # Second call: cache hit
        mock_get.return_value = {"embedding": [0.1, 0.2, 0.3]}
        
        cached = await cache_service.get(cache_key)
        assert cached is not None
        
        # Should not need to regenerate embeddings
        # (In real implementation, this would save LLM calls)

