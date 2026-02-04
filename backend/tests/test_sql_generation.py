"""
Comprehensive tests for SQL Generation Agent.
Tests SQL generation from query understanding with various query types.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.sql_generation import SQLGenerationAgent
from app.core.redis_client import cache_service


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("customers", "id", "integer"),
        ("customers", "company_name", "varchar"),
        ("customers", "city", "varchar"),
        ("sales_orders", "id", "integer"),
        ("sales_orders", "customer_id", "integer"),
        ("sales_orders", "total_amount", "numeric"),
        ("sales_orders", "order_date", "date"),
        ("products", "id", "integer"),
        ("products", "name", "varchar"),
        ("products", "price", "numeric"),
        ("products", "category", "varchar"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


@pytest.fixture
def sql_agent(mock_db):
    """Create a SQLGenerationAgent instance for testing."""
    return SQLGenerationAgent(db=mock_db)


@pytest.mark.asyncio
async def test_simple_sql_generation(sql_agent):
    """Test simple SQL generation: 'How many customers?'"""
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
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, company_name, city)"
        mock_parse.return_value = {"customers": ["id", "company_name", "city"]}
        mock_ground.return_value = query_understanding
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="How many customers?"
        )
        
        assert "SELECT" in sql.upper()
        assert "customers" in sql.lower()
        assert "COUNT" in sql.upper()


@pytest.mark.asyncio
async def test_join_query_generation(sql_agent):
    """Test JOIN query generation: 'Show customer names with their order totals'"""
    query_understanding = {
        "intent": "Retrieve customer names with aggregated order totals",
        "tables": ["customers", "sales_orders"],
        "columns": ["company_name", "total_amount"],
        "filters": [],
        "aggregations": ["SUM"],
        "group_by": ["company_name"],
        "order_by": None,
        "limit": None,
        "ambiguities": [],
        "needs_clarification": False
    }
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, company_name), sales_orders (id, customer_id, total_amount)"
        mock_parse.return_value = {
            "customers": ["id", "company_name"],
            "sales_orders": ["id", "customer_id", "total_amount"]
        }
        mock_ground.return_value = query_understanding
        mock_llm.return_value = """SELECT c.company_name, SUM(o.total_amount) 
                                   FROM customers c 
                                   JOIN sales_orders o ON c.id = o.customer_id 
                                   GROUP BY c.company_name;"""
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="Show customer names with their order totals"
        )
        
        assert "SELECT" in sql.upper()
        assert "JOIN" in sql.upper() or "join" in sql.lower()
        assert "SUM" in sql.upper()
        assert "GROUP BY" in sql.upper() or "group by" in sql.lower()


@pytest.mark.asyncio
async def test_complex_aggregation_generation(sql_agent):
    """Test complex aggregation: 'Average order value by customer type'"""
    query_understanding = {
        "intent": "Calculate average order value grouped by customer type",
        "tables": ["customers", "sales_orders"],
        "columns": ["customer_type", "total_amount"],
        "filters": [],
        "aggregations": ["AVG"],
        "group_by": ["customer_type"],
        "order_by": None,
        "limit": None,
        "ambiguities": [],
        "needs_clarification": False
    }
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, customer_type), sales_orders (id, customer_id, total_amount)"
        mock_parse.return_value = {
            "customers": ["id", "customer_type"],
            "sales_orders": ["id", "customer_id", "total_amount"]
        }
        mock_ground.return_value = query_understanding
        mock_llm.return_value = """SELECT c.customer_type, AVG(o.total_amount) 
                                   FROM customers c 
                                   JOIN sales_orders o ON c.id = o.customer_id 
                                   GROUP BY c.customer_type;"""
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="Average order value by customer type"
        )
        
        assert "AVG" in sql.upper()
        assert "GROUP BY" in sql.upper() or "group by" in sql.lower()


@pytest.mark.asyncio
async def test_time_based_query_generation(sql_agent):
    """Test time-based query: 'Sales by month in 2024'"""
    query_understanding = {
        "intent": "Calculate sales grouped by month for year 2024",
        "tables": ["sales_orders"],
        "columns": ["order_date", "total_amount"],
        "filters": [
            {"column": "order_date", "operator": ">=", "value": "2024-01-01", "type": "date"},
            {"column": "order_date", "operator": "<", "value": "2025-01-01", "type": "date"}
        ],
        "aggregations": ["SUM"],
        "group_by": ["month"],
        "order_by": None,
        "limit": None,
        "ambiguities": [],
        "needs_clarification": False
    }
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "sales_orders (id, order_date, total_amount)"
        mock_parse.return_value = {
            "sales_orders": ["id", "order_date", "total_amount"]
        }
        mock_ground.return_value = query_understanding
        mock_llm.return_value = """SELECT DATE_TRUNC('month', order_date) as month, 
                                   SUM(total_amount) as total_sales
                                   FROM sales_orders 
                                   WHERE order_date >= '2024-01-01' 
                                   GROUP BY month;"""
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="Sales by month in 2024"
        )
        
        assert "DATE_TRUNC" in sql.upper() or "date_trunc" in sql.lower()
        assert "2024" in sql
        assert "SUM" in sql.upper()
        assert "WHERE" in sql.upper() or "where" in sql.lower()


@pytest.mark.asyncio
async def test_multi_table_join_generation(sql_agent):
    """Test multi-table JOIN: 'Product sales by category and warehouse'"""
    query_understanding = {
        "intent": "Retrieve product sales grouped by category and warehouse",
        "tables": ["products", "sales_order_items", "sales_orders", "inventory", "warehouses"],
        "columns": ["category", "warehouse_name", "quantity", "price"],
        "filters": [],
        "aggregations": ["SUM"],
        "group_by": ["category", "warehouse_name"],
        "order_by": None,
        "limit": None,
        "ambiguities": [],
        "needs_clarification": False
    }
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "products (id, name, category), sales_order_items (id, product_id, quantity), sales_orders (id), inventory (product_id, warehouse_id), warehouses (id, name)"
        mock_parse.return_value = {
            "products": ["id", "name", "category"],
            "sales_order_items": ["id", "product_id", "quantity"],
            "sales_orders": ["id"],
            "inventory": ["product_id", "warehouse_id"],
            "warehouses": ["id", "name"]
        }
        mock_ground.return_value = query_understanding
        mock_llm.return_value = """SELECT p.category, w.name as warehouse_name, 
                                   SUM(soi.quantity * soi.price) as total_sales
                                   FROM products p
                                   JOIN sales_order_items soi ON p.id = soi.product_id
                                   JOIN sales_orders so ON soi.order_id = so.id
                                   JOIN inventory i ON p.id = i.product_id
                                   JOIN warehouses w ON i.warehouse_id = w.id
                                   GROUP BY p.category, w.name;"""
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="Product sales by category and warehouse"
        )
        
        # Should have multiple JOINs
        join_count = sql.upper().count("JOIN")
        assert join_count >= 2
        assert "GROUP BY" in sql.upper() or "group by" in sql.lower()


@pytest.mark.asyncio
async def test_sql_generation_with_rag(sql_agent):
    """Test SQL generation with RAG context retrieval."""
    query_understanding = {
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
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.hybrid_rag, 'search', new_callable=AsyncMock) as mock_rag_search, \
         patch.object(sql_agent.hybrid_rag, 'format_context', new_callable=MagicMock) as mock_rag_format, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, company_name)"
        mock_parse.return_value = {"customers": ["id", "company_name"]}
        mock_ground.return_value = query_understanding
        mock_rag_search.return_value = [{"table": "customers", "relevance": 0.9}]
        mock_rag_format.return_value = "Additional context: customers table"
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="How many customers?",
            use_rag=True
        )
        
        assert mock_rag_search.called
        assert "SELECT" in sql.upper()


@pytest.mark.asyncio
async def test_sql_generation_without_rag(sql_agent):
    """Test SQL generation without RAG (use_rag=False)."""
    query_understanding = {
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
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, company_name)"
        mock_parse.return_value = {"customers": ["id", "company_name"]}
        mock_ground.return_value = query_understanding
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="How many customers?",
            use_rag=False
        )
        
        assert "SELECT" in sql.upper()
        assert "customers" in sql.lower()


@pytest.mark.asyncio
async def test_sql_generation_with_previous_error(sql_agent):
    """Test SQL generation with previous error for self-correction."""
    query_understanding = {
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
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground, \
         patch.object(sql_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        
        mock_schema.return_value = "customers (id, company_name)"
        mock_parse.return_value = {"customers": ["id", "company_name"]}
        mock_ground.return_value = query_understanding
        mock_llm.return_value = "SELECT COUNT(*) FROM customers;"
        
        sql = await sql_agent.generate_sql(
            query_understanding=query_understanding,
            natural_language_query="How many customers?",
            previous_error="Table 'customer' does not exist",
            previous_sql="SELECT COUNT(*) FROM customer;"
        )
        
        assert "SELECT" in sql.upper()
        # Should use corrected table name
        assert "customers" in sql.lower()


@pytest.mark.asyncio
async def test_sql_generation_empty_tables(sql_agent):
    """Test SQL generation with empty tables (should raise error)."""
    query_understanding = {
        "intent": "Query with no valid tables",
        "tables": [],
        "columns": [],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None,
        "limit": None,
        "ambiguities": ["No valid tables identified"],
        "needs_clarification": True
    }
    
    with patch.object(sql_agent, '_get_dynamic_schema_info', new_callable=AsyncMock) as mock_schema, \
         patch.object(sql_agent, '_parse_schema_info', new_callable=AsyncMock) as mock_parse, \
         patch.object(sql_agent, '_ground_query_understanding', new_callable=AsyncMock) as mock_ground:
        
        mock_schema.return_value = ""
        mock_parse.return_value = {}
        mock_ground.return_value = query_understanding
        
        with pytest.raises(ValueError, match="(?i)no valid tables|cannot generate sql"):
            await sql_agent.generate_sql(
                query_understanding=query_understanding,
                natural_language_query="Show me bottles"
            )

