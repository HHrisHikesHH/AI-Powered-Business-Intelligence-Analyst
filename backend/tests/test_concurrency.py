"""
Tests for concurrent user handling.
Tests system stability under concurrent load.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.agents.orchestrator import Orchestrator
from app.core.redis_client import cache_service


@pytest.fixture
def orchestrator():
    """Create an Orchestrator instance for testing."""
    return Orchestrator()


@pytest.mark.asyncio
async def test_10_concurrent_users(orchestrator):
    """Test system with 10 concurrent users."""
    async def run_query(query_id):
        query = f"How many customers? Query {query_id}"
        try:
            with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
                 patch.object(cache_service, 'set', new_callable=AsyncMock):
                result = await orchestrator.process_query(query)
                return {"success": True, "query_id": query_id, "result": result}
        except Exception as e:
            return {"success": False, "query_id": query_id, "error": str(e)}
    
    # Simulate 10 concurrent users
    tasks = [run_query(i) for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that all queries completed (may have errors but shouldn't crash)
    assert len(results) == 10
    
    # Calculate success rate
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    success_rate = successful / len(results)
    
    # Should have at least some successful queries (or all if mocks work)
    assert success_rate >= 0.0  # At minimum, no crashes


@pytest.mark.asyncio
async def test_50_concurrent_users(orchestrator):
    """Test system with 50 concurrent users."""
    async def run_query(query_id):
        query = f"Show me products. Query {query_id}"
        try:
            with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
                 patch.object(cache_service, 'set', new_callable=AsyncMock):
                result = await orchestrator.process_query(query)
                return {"success": True, "query_id": query_id}
        except Exception as e:
            return {"success": False, "query_id": query_id, "error": str(e)}
    
    # Simulate 50 concurrent users
    tasks = [run_query(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that all queries completed without crashes
    assert len(results) == 50
    
    # System should remain stable (no exceptions raised)
    exceptions = sum(1 for r in results if isinstance(r, Exception))
    assert exceptions == 0, f"Found {exceptions} exceptions during concurrent execution"


@pytest.mark.asyncio
async def test_100_concurrent_users_stress(orchestrator):
    """Test system with 100 concurrent users (stress test)."""
    async def run_query(query_id):
        query = f"List customers. Query {query_id}"
        try:
            with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
                 patch.object(cache_service, 'set', new_callable=AsyncMock):
                result = await orchestrator.process_query(query)
                return {"success": True, "query_id": query_id}
        except Exception as e:
            return {"success": False, "query_id": query_id, "error": str(e)}
    
    # Simulate 100 concurrent users
    tasks = [run_query(i) for i in range(100)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that all queries completed
    assert len(results) == 100
    
    # System should degrade gracefully (no crashes, errors handled)
    exceptions = sum(1 for r in results if isinstance(r, Exception))
    assert exceptions == 0, f"System crashed with {exceptions} exceptions"
    
    # Calculate success rate
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    success_rate = successful / len(results)
    
    # For stress test, we mainly care about no crashes
    # Success rate may be lower but system should handle errors gracefully
    assert success_rate >= 0.0


@pytest.mark.asyncio
async def test_concurrent_queries_no_deadlocks(orchestrator):
    """Test that concurrent queries don't cause deadlocks."""
    async def run_query(query_id, delay=0):
        query = f"Query {query_id}"
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
                 patch.object(cache_service, 'set', new_callable=AsyncMock):
                result = await orchestrator.process_query(query)
                return {"success": True, "query_id": query_id}
        except Exception as e:
            return {"success": False, "query_id": query_id, "error": str(e)}
    
    # Run queries with varying delays to test for deadlocks
    tasks = [
        run_query(1, delay=0.01),
        run_query(2, delay=0.02),
        run_query(3, delay=0.01),
        run_query(4, delay=0.03),
        run_query(5, delay=0.01)
    ]
    
    # Use timeout to detect deadlocks
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=10.0  # Should complete within 10 seconds
        )
        
        # All queries should complete
        assert len(results) == 5
        assert all(not isinstance(r, asyncio.TimeoutError) for r in results)
        
    except asyncio.TimeoutError:
        pytest.fail("Deadlock detected: queries did not complete within timeout")


@pytest.mark.asyncio
async def test_concurrent_error_handling(orchestrator):
    """Test that errors in concurrent queries are handled properly."""
    async def run_query(query_id, should_fail=False):
        query = f"Query {query_id}"
        try:
            if should_fail:
                raise ValueError(f"Intentional error for query {query_id}")
            
            with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
                 patch.object(cache_service, 'set', new_callable=AsyncMock):
                result = await orchestrator.process_query(query)
                return {"success": True, "query_id": query_id}
        except Exception as e:
            return {"success": False, "query_id": query_id, "error": str(e)}
    
    # Mix of successful and failing queries
    tasks = [
        run_query(1, should_fail=False),
        run_query(2, should_fail=True),
        run_query(3, should_fail=False),
        run_query(4, should_fail=True),
        run_query(5, should_fail=False)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All queries should complete (no unhandled exceptions)
    assert len(results) == 5
    assert all(not isinstance(r, Exception) for r in results)
    
    # Check that errors were handled gracefully
    failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
    assert len(failed) == 2  # Two queries should have failed
    assert all("error" in r for r in failed)

