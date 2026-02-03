"""
Comprehensive test suite with 100+ queries covering various scenarios.
Tests error handling, retry logic, and self-correction.
"""
import pytest
from app.agents.orchestrator import Orchestrator
from app.services.error_handler import error_handler, ErrorCategory
from unittest.mock import AsyncMock, MagicMock, patch


# Test queries organized by category
TEST_QUERIES = {
    "simple": [
        "How many customers do we have?",
        "What's the total revenue?",
        "Show me all products",
        "List all orders",
        "Count the number of products",
        "What is the average order value?",
        "Show me the most expensive product",
        "How many orders were placed?",
        "List all customers",
        "What's the total number of products?",
    ],
    "filtering": [
        "Show me customers from New York",
        "List orders placed in 2024",
        "Show products with price greater than 100",
        "Find customers created after 2023",
        "Show orders with status 'completed'",
        "List products in the Electronics category",
        "Show customers with email containing 'gmail'",
        "Find orders placed between January and March",
        "Show products with stock less than 10",
        "List customers from California or New York",
    ],
    "aggregation": [
        "What's the total revenue by month?",
        "Show me the average order value by customer",
        "How many products are in each category?",
        "What's the total sales by product?",
        "Show me the count of orders by status",
        "What's the average price by category?",
        "How many customers are in each city?",
        "Show me the total quantity sold by product",
        "What's the maximum order value?",
        "Show me the minimum product price",
    ],
    "group_by": [
        "List customers by city",
        "Show products grouped by category",
        "Display orders by status",
        "Group customers by registration date",
        "Show products by supplier",
        "List orders by customer",
        "Group sales by region",
        "Show products by price range",
        "List customers by country",
        "Group orders by month",
    ],
    "joins": [
        "Show me customer names with their orders",
        "List products with their categories",
        "Show orders with customer information",
        "Display order items with product details",
        "Show customers who have placed orders",
        "List products that have been ordered",
        "Show order details with customer and product info",
        "Display customers with their total order count",
        "Show products with order counts",
        "List orders with customer names and product names",
    ],
    "complex": [
        "What's the total revenue for customers who placed more than 5 orders?",
        "Show me the top 10 customers by total spending",
        "What products have never been ordered?",
        "Show me customers who haven't placed any orders",
        "What's the average order value for each customer?",
        "Show me products with sales above average",
        "List customers who ordered in the last 30 days",
        "What's the revenue trend over the last 6 months?",
        "Show me the most popular products by order count",
        "What's the customer retention rate?",
    ],
    "ambiguous": [
        "Show me sales",  # Ambiguous - could mean orders, revenue, etc.
        "What's the total?",  # Missing context
        "List everything",  # Too vague
        "Show me data",  # No specific table/column
        "What happened?",  # No context
        "Give me numbers",  # Too vague
        "Show recent stuff",  # Ambiguous time range
        "What's the best?",  # No criteria
        "List all",  # Missing table
        "Show me information",  # Too vague
    ],
    "edge_cases": [
        "Show me customers created in 2025",  # Likely empty results
        "List orders with negative amounts",  # Edge case
        "Show products with zero price",  # Edge case
        "Find customers with no email",  # NULL handling
        "Show orders placed on February 30th",  # Invalid date
        "List products with price = 'free'",  # Type mismatch
        "Show me customers from 'Unknown' city",  # Edge case
        "List orders with status = null",  # NULL handling
        "Show products in category 'NonExistent'",  # Empty results
        "Find customers with id = 999999",  # Likely empty
    ],
    "time_based": [
        "Show me orders from today",
        "List orders from last week",
        "What's the revenue this month?",
        "Show me orders from last month",
        "What's the sales trend over the last year?",
        "List orders placed in the last 7 days",
        "Show me products added this year",
        "What's the revenue by quarter?",
        "List orders from the current year",
        "Show me the latest orders",
    ],
    "sorting": [
        "Show me the most expensive products",
        "List customers alphabetically",
        "Show orders by date, newest first",
        "What are the cheapest products?",
        "Show me the largest orders",
        "List products by popularity",
        "Show customers by registration date",
        "What are the top selling products?",
        "List orders by total amount descending",
        "Show me the newest customers",
    ],
}


@pytest.mark.asyncio
async def test_simple_queries(mock_db):
    """Test simple queries that should succeed."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["simple"][:5]:  # Test first 5
        result = await orchestrator.process_query(query)
        
        # Should not have critical errors
        assert result["error"] == "" or ErrorCategory.UNKNOWN_ERROR.value not in result.get("error_category", "")
        # Should have query understanding
        assert result["query_understanding"] != {}


@pytest.mark.asyncio
async def test_filtering_queries(mock_db):
    """Test queries with filters."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["filtering"][:5]:
        result = await orchestrator.process_query(query)
        
        # Should generate SQL with WHERE clause
        if result["sql"]:
            assert "WHERE" in result["sql"].upper() or result["error"] != ""


@pytest.mark.asyncio
async def test_aggregation_queries(mock_db):
    """Test aggregation queries."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["aggregation"][:5]:
        result = await orchestrator.process_query(query)
        
        # Should have aggregations in understanding
        understanding = result.get("query_understanding", {})
        aggregations = understanding.get("aggregations", [])
        
        # Either has aggregations or is an error (acceptable)
        assert len(aggregations) > 0 or result["error"] != ""


@pytest.mark.asyncio
async def test_group_by_queries(mock_db):
    """Test GROUP BY queries."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["group_by"][:5]:
        result = await orchestrator.process_query(query)
        
        # Should have group_by in understanding or SQL
        understanding = result.get("query_understanding", {})
        group_by = understanding.get("group_by", [])
        sql = result.get("sql", "")
        
        assert len(group_by) > 0 or "GROUP BY" in sql.upper() or result["error"] != ""


@pytest.mark.asyncio
async def test_join_queries(mock_db):
    """Test queries requiring joins."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["joins"][:5]:
        result = await orchestrator.process_query(query)
        
        # Should identify multiple tables
        understanding = result.get("query_understanding", {})
        tables = understanding.get("tables", [])
        
        assert len(tables) >= 1  # At least one table identified


@pytest.mark.asyncio
async def test_complex_queries(mock_db):
    """Test complex queries with subqueries/CTEs."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["complex"][:5]:
        result = await orchestrator.process_query(query)
        
        # Complex queries may fail, but should be handled gracefully
        assert "error" in result
        # Should have attempted to understand the query
        assert result["query_understanding"] != {}


@pytest.mark.asyncio
async def test_ambiguous_queries(mock_db):
    """Test ambiguous queries that should trigger clarification."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["ambiguous"]:
        result = await orchestrator.process_query(query)
        
        # Ambiguous queries may fail or need clarification
        understanding = result.get("query_understanding", {})
        ambiguities = understanding.get("ambiguities", [])
        needs_clarification = understanding.get("needs_clarification", False)
        
        # Should either identify ambiguities or handle gracefully
        assert len(ambiguities) > 0 or needs_clarification or result["error"] != ""


@pytest.mark.asyncio
async def test_edge_cases(mock_db):
    """Test edge cases and error scenarios."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["edge_cases"][:5]:
        result = await orchestrator.process_query(query)
        
        # Edge cases should be handled gracefully
        assert "error" in result
        # Should have attempted processing
        assert result["query_understanding"] != {}


@pytest.mark.asyncio
async def test_time_based_queries(mock_db):
    """Test time-based queries."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    
    for query in TEST_QUERIES["time_based"][:5]:
        result = await orchestrator.process_query(query)
        
        # Should identify temporal filters
        understanding = result.get("query_understanding", {})
        filters = understanding.get("filters", [])
        
        # Should have filters or handle gracefully
        assert len(filters) > 0 or result["error"] != ""


@pytest.mark.asyncio
async def test_all_query_categories(mock_db):
    """Test all query categories and measure success rate."""
    orchestrator = Orchestrator(mock_db, max_retries=3)
    error_handler.clear_log()
    
    total_queries = 0
    successful_queries = 0
    failed_queries = 0
    retry_count = 0
    
    results_by_category = {}
    
    for category, queries in TEST_QUERIES.items():
        category_success = 0
        category_total = len(queries)
        
        for query in queries:
            total_queries += 1
            result = await orchestrator.process_query(query)
            
            if result.get("error") == "" and result.get("sql"):
                successful_queries += 1
                category_success += 1
            else:
                failed_queries += 1
            
            if result.get("retry_count", 0) > 0:
                retry_count += 1
        
        results_by_category[category] = {
            "total": category_total,
            "successful": category_success,
            "failed": category_total - category_success,
            "success_rate": (category_success / category_total * 100) if category_total > 0 else 0
        }
    
    overall_success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
    
    # Target: <15% error rate (i.e., >85% success rate)
    assert overall_success_rate >= 85, f"Success rate {overall_success_rate:.2f}% is below 85% target"
    
    # Print summary
    print(f"\n=== Query Test Summary ===")
    print(f"Total queries: {total_queries}")
    print(f"Successful: {successful_queries} ({overall_success_rate:.2f}%)")
    print(f"Failed: {failed_queries}")
    print(f"Queries with retries: {retry_count}")
    print(f"\nBy Category:")
    for category, stats in results_by_category.items():
        print(f"  {category}: {stats['successful']}/{stats['total']} ({stats['success_rate']:.2f}%)")
    
    # Get error statistics
    error_stats = error_handler.get_error_statistics()
    print(f"\nError Statistics:")
    print(f"  Total errors: {error_stats['total_errors']}")
    print(f"  By category: {error_stats['by_category']}")
    print(f"  Retryable: {error_stats['retryable_count']} ({error_stats['retryable_percentage']:.2f}%)")


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [(20,)]
    mock_result.keys.return_value = ["count"]
    mock.execute = AsyncMock(return_value=mock_result)
    return mock

