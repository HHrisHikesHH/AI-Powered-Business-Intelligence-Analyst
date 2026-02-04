"""
Comprehensive tests for Query Understanding Agent.
Tests natural language query parsing and intent extraction.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.agents.query_understanding import QueryUnderstandingAgent
from app.core.redis_client import cache_service


@pytest.fixture
def query_agent():
    """Create a QueryUnderstandingAgent instance for testing."""
    return QueryUnderstandingAgent()


@pytest.mark.asyncio
async def test_simple_query_customers_count(query_agent):
    """Test simple query: 'How many customers do we have?'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
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
        })
        
        result = await query_agent.understand("How many customers do we have?")
        
        assert result["intent"] == "Count total number of customers"
        assert "customers" in result["tables"]
        assert "COUNT" in result["aggregations"]
        assert result["needs_clarification"] is False
        assert len(result["ambiguities"]) == 0


@pytest.mark.asyncio
async def test_simple_query_show_employees(query_agent):
    """Test simple query: 'Show me all employees'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve all employees",
            "tables": ["employees"],
            "columns": ["id", "first_name", "last_name", "email", "department_id"],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Show me all employees")
        
        assert result["intent"] == "Retrieve all employees"
        assert "employees" in result["tables"]
        assert len(result["filters"]) == 0
        assert result["needs_clarification"] is False


@pytest.mark.asyncio
async def test_simple_query_list_products(query_agent):
    """Test simple query: 'List all products'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve all products",
            "tables": ["products"],
            "columns": ["id", "name", "category", "price", "stock_quantity"],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("List all products")
        
        assert result["intent"] == "Retrieve all products"
        assert "products" in result["tables"]
        assert result["needs_clarification"] is False


@pytest.mark.asyncio
async def test_filtered_query_customers_new_york(query_agent):
    """Test filtered query: 'Show customers from New York'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve customers filtered by location",
            "tables": ["customers"],
            "columns": ["id", "company_name", "city", "state"],
            "filters": [
                {"column": "city", "operator": "=", "value": "New York", "type": "string"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Show customers from New York")
        
        assert result["intent"] == "Retrieve customers filtered by location"
        assert "customers" in result["tables"]
        assert len(result["filters"]) > 0
        assert any(f["column"] == "city" for f in result["filters"])
        assert any(f["value"] == "New York" for f in result["filters"])


@pytest.mark.asyncio
async def test_filtered_query_employees_2024(query_agent):
    """Test filtered query: 'Employees hired in 2024'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve employees hired in specific year",
            "tables": ["employees"],
            "columns": ["id", "first_name", "last_name", "hire_date"],
            "filters": [
                {"column": "hire_date", "operator": ">=", "value": "2024-01-01", "type": "date"},
                {"column": "hire_date", "operator": "<", "value": "2025-01-01", "type": "date"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Employees hired in 2024")
        
        assert result["intent"] == "Retrieve employees hired in specific year"
        assert "employees" in result["tables"]
        assert len(result["filters"]) > 0
        assert any("hire_date" in f["column"] for f in result["filters"])


@pytest.mark.asyncio
async def test_filtered_query_products_price(query_agent):
    """Test filtered query: 'Products with price > 1000'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve products filtered by price",
            "tables": ["products"],
            "columns": ["id", "name", "price", "category"],
            "filters": [
                {"column": "price", "operator": ">", "value": 1000, "type": "number"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Products with price > 1000")
        
        assert result["intent"] == "Retrieve products filtered by price"
        assert "products" in result["tables"]
        assert len(result["filters"]) > 0
        assert any(f["column"] == "price" and f["operator"] == ">" for f in result["filters"])


@pytest.mark.asyncio
async def test_aggregation_query_revenue_by_month(query_agent):
    """Test aggregation query: 'Total revenue by month'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Calculate total revenue grouped by month",
            "tables": ["invoices", "sales_orders"],
            "columns": ["total_amount", "order_date", "invoice_date"],
            "filters": [],
            "aggregations": ["SUM"],
            "group_by": ["month"],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Total revenue by month")
        
        assert result["intent"] == "Calculate total revenue grouped by month"
        assert len(result["aggregations"]) > 0
        assert "SUM" in result["aggregations"]
        assert len(result["group_by"]) > 0


@pytest.mark.asyncio
async def test_aggregation_query_avg_salary_by_department(query_agent):
    """Test aggregation query: 'Average salary by department'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Calculate average salary grouped by department",
            "tables": ["employees", "departments"],
            "columns": ["salary", "department_id", "department_name"],
            "filters": [],
            "aggregations": ["AVG"],
            "group_by": ["department_id"],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Average salary by department")
        
        assert result["intent"] == "Calculate average salary grouped by department"
        assert "AVG" in result["aggregations"]
        assert len(result["group_by"]) > 0
        assert any("department" in gb.lower() for gb in result["group_by"])


@pytest.mark.asyncio
async def test_aggregation_query_count_orders_by_status(query_agent):
    """Test aggregation query: 'Count of orders by status'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Count orders grouped by status",
            "tables": ["sales_orders"],
            "columns": ["id", "status"],
            "filters": [],
            "aggregations": ["COUNT"],
            "group_by": ["status"],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Count of orders by status")
        
        assert result["intent"] == "Count orders grouped by status"
        assert "COUNT" in result["aggregations"]
        assert len(result["group_by"]) > 0
        assert any("status" in gb.lower() for gb in result["group_by"])


@pytest.mark.asyncio
async def test_complex_query_top_customers(query_agent):
    """Test complex query: 'Top 10 customers by total order value'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve top customers by aggregated order value",
            "tables": ["customers", "sales_orders"],
            "columns": ["customer_id", "company_name", "total_amount"],
            "filters": [],
            "aggregations": ["SUM"],
            "group_by": ["customer_id"],
            "order_by": {"column": "total_amount", "direction": "DESC"},
            "limit": 10,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Top 10 customers by total order value")
        
        assert result["intent"] == "Retrieve top customers by aggregated order value"
        assert result["limit"] == 10
        assert result["order_by"] is not None
        assert result["order_by"]["direction"] == "DESC"
        assert "SUM" in result["aggregations"]


@pytest.mark.asyncio
async def test_complex_query_employees_performance(query_agent):
    """Test complex query: 'Employees with performance rating > 4.0'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve employees filtered by performance rating",
            "tables": ["employees"],
            "columns": ["id", "first_name", "last_name", "performance_rating"],
            "filters": [
                {"column": "performance_rating", "operator": ">", "value": 4.0, "type": "number"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Employees with performance rating > 4.0")
        
        assert result["intent"] == "Retrieve employees filtered by performance rating"
        assert "employees" in result["tables"]
        assert len(result["filters"]) > 0
        assert any(f["column"] == "performance_rating" and f["operator"] == ">" for f in result["filters"])


@pytest.mark.asyncio
async def test_complex_query_low_inventory(query_agent):
    """Test complex query: 'Products with low inventory across all warehouses'"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve products with low inventory levels",
            "tables": ["products", "inventory", "warehouses"],
            "columns": ["product_id", "product_name", "warehouse_id", "quantity_on_hand"],
            "filters": [
                {"column": "quantity_on_hand", "operator": "<", "value": 10, "type": "number"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        })
        
        result = await query_agent.understand("Products with low inventory across all warehouses")
        
        assert result["intent"] == "Retrieve products with low inventory levels"
        assert len(result["tables"]) >= 2
        assert "products" in result["tables"]
        assert len(result["filters"]) > 0


@pytest.mark.asyncio
async def test_ambiguous_query_show_sales(query_agent):
    """Test ambiguous query: 'Show me sales' (needs clarification)"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve sales information",
            "tables": [],
            "columns": [],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [
                "Unclear what 'sales' refers to - could be sales_orders, sales_revenue, sales_team, etc."
            ],
            "needs_clarification": True
        })
        
        result = await query_agent.understand("Show me sales")
        
        assert result["needs_clarification"] is True
        assert len(result["ambiguities"]) > 0
        # Should not default to any table if ambiguous
        assert len(result["tables"]) == 0 or "sales" in str(result["ambiguities"]).lower()


@pytest.mark.asyncio
async def test_ambiguous_query_revenue_last_year(query_agent):
    """Test ambiguous query: 'Revenue last year' (which year?)"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Calculate revenue for previous year",
            "tables": ["invoices", "sales_orders"],
            "columns": ["total_amount", "order_date", "invoice_date"],
            "filters": [],
            "aggregations": ["SUM"],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [
                "Unclear which specific year 'last year' refers to - needs current date context"
            ],
            "needs_clarification": False  # Can proceed with relative date
        })
        
        result = await query_agent.understand("Revenue last year")
        
        assert len(result["ambiguities"]) > 0 or result["needs_clarification"] is False
        assert "SUM" in result["aggregations"]


@pytest.mark.asyncio
async def test_ambiguous_query_best_employee(query_agent):
    """Test ambiguous query: 'Best performing employee' (by what metric?)"""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "intent": "Retrieve top performing employee",
            "tables": ["employees"],
            "columns": ["id", "first_name", "last_name", "performance_rating", "sales_target", "sales_achieved"],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": {"column": "performance_rating", "direction": "DESC"},
            "limit": 1,
            "ambiguities": [
                "Unclear metric for 'best' - could be performance_rating, sales_achieved, or other criteria"
            ],
            "needs_clarification": True
        })
        
        result = await query_agent.understand("Best performing employee")
        
        assert result["needs_clarification"] is True
        assert len(result["ambiguities"]) > 0
        assert "employees" in result["tables"]


@pytest.mark.asyncio
async def test_caching(query_agent):
    """Test that query understanding results are cached."""
    query = "How many customers do we have?"
    expected_result = {
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
    
    # Mock cache to return None first time (cache miss), then return cached value
    with patch.object(cache_service, 'get', new_callable=AsyncMock) as mock_cache_get, \
         patch.object(cache_service, 'set', new_callable=AsyncMock) as mock_cache_set, \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        # First call: cache miss, LLM called
        mock_cache_get.return_value = None
        mock_llm.return_value = json.dumps(expected_result)
        
        result1 = await query_agent.understand(query)
        
        assert result1 == expected_result
        assert mock_cache_get.called
        assert mock_cache_set.called  # Should cache the result
        
        # Second call: cache hit, LLM not called
        mock_cache_get.return_value = expected_result
        mock_llm.reset_mock()
        
        result2 = await query_agent.understand(query)
        
        assert result2 == expected_result
        # LLM should not be called on cache hit
        assert not mock_llm.called


@pytest.mark.asyncio
async def test_json_parsing_with_markdown(query_agent):
    """Test that JSON parsing handles markdown code blocks."""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        # LLM sometimes returns JSON wrapped in markdown
        mock_llm.return_value = """```json
{
    "intent": "Count customers",
    "tables": ["customers"],
    "columns": ["id"],
    "filters": [],
    "aggregations": ["COUNT"],
    "group_by": [],
    "order_by": null,
    "limit": null,
    "ambiguities": [],
    "needs_clarification": false
}
```"""
        
        result = await query_agent.understand("How many customers?")
        
        assert result["intent"] == "Count customers"
        assert "customers" in result["tables"]


@pytest.mark.asyncio
async def test_fallback_on_json_parse_error(query_agent):
    """Test fallback behavior when JSON parsing fails."""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        # Return invalid JSON
        mock_llm.return_value = "This is not valid JSON {"
        
        result = await query_agent.understand("Show me customers")
        
        # Should return fallback understanding
        assert "intent" in result
        assert "tables" in result
        assert "customers" in result["tables"]  # Fallback should detect "customers" keyword
        assert result["needs_clarification"] is True  # Fallback marks as needing clarification


@pytest.mark.asyncio
async def test_fallback_empty_tables_on_unknown_entity(query_agent):
    """Test that fallback returns empty tables for unknown entities."""
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(query_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        # Return invalid JSON for query about non-existent entity
        mock_llm.return_value = "Invalid JSON {"
        
        result = await query_agent.understand("Show me bottles")
        
        # Fallback should not default to customers table
        assert "intent" in result
        assert isinstance(result["tables"], list)
        # Should not contain "customers" if query was about "bottles"
        assert "customers" not in result["tables"] or len(result["tables"]) == 0
        assert result["needs_clarification"] is True

