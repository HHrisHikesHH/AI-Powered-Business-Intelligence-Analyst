"""
Unit tests for agents.
"""
import pytest
from app.agents.query_understanding import QueryUnderstandingAgent
from app.agents.sql_generation import SQLGenerationAgent
from app.agents.sql_validator import SQLValidator
from app.agents.analysis import AnalysisAgent
from app.agents.visualization import VisualizationAgent
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


@pytest.mark.asyncio
async def test_analysis_agent():
    """Test Analysis Agent."""
    agent = AnalysisAgent()
    
    query_understanding = {
        "intent": "Count total number of customers",
        "tables": ["customers"],
        "columns": ["id"],
        "filters": [],
        "aggregations": ["COUNT"],
        "group_by": [],
        "order_by": None
    }
    
    results = [{"customer_count": 20}]
    
    # Mock LLM response
    with patch.object(agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '''{
            "insights": ["Total customer count is 20"],
            "trends": [],
            "anomalies": [],
            "recommendations": ["Monitor customer growth"],
            "summary": "The query returned a customer count of 20."
        }'''
        
        analysis = await agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="How many customers do we have?",
            sql="SELECT COUNT(*) as customer_count FROM customers;",
            results=results
        )
        
        assert "insights" in analysis
        assert len(analysis["insights"]) > 0
        assert "summary" in analysis
        assert "recommendations" in analysis


@pytest.mark.asyncio
async def test_analysis_agent_empty_results():
    """Test Analysis Agent with empty results."""
    agent = AnalysisAgent()
    
    query_understanding = {
        "intent": "Find customers",
        "tables": ["customers"],
        "columns": [],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    analysis = await agent.analyze_results(
        query_understanding=query_understanding,
        natural_language_query="Show me customers",
        sql="SELECT * FROM customers WHERE id = 999;",
        results=[]
    )
    
    assert "insights" in analysis
    assert "anomalies" in analysis
    assert len(analysis["anomalies"]) > 0
    assert "No results found" in analysis["insights"][0] or "zero results" in analysis["summary"].lower()


@pytest.mark.asyncio
async def test_visualization_agent():
    """Test Visualization Agent."""
    agent = VisualizationAgent()
    
    query_understanding = {
        "intent": "Show products by category",
        "tables": ["products"],
        "columns": ["category", "count"],
        "filters": [],
        "aggregations": ["COUNT"],
        "group_by": ["category"],
        "order_by": None
    }
    
    results = [
        {"category": "Electronics", "product_count": 10},
        {"category": "Clothing", "product_count": 5}
    ]
    
    # Mock LLM response
    with patch.object(agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '''{
            "chart_type": "bar",
            "data_key": "product_count",
            "category_key": "category",
            "title": "Products by Category",
            "description": "Bar chart showing product count by category",
            "x_axis_label": "Category",
            "y_axis_label": "Product Count",
            "colors": ["#8884d8", "#82ca9d"],
            "config": {
                "width": 800,
                "height": 400,
                "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
            }
        }'''
        
        visualization = await agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Show me products by category",
            sql="SELECT category, COUNT(*) as product_count FROM products GROUP BY category;",
            results=results
        )
        
        assert "chart_type" in visualization
        assert "data_key" in visualization
        assert "category_key" in visualization
        assert "recharts_component" in visualization
        assert visualization["chart_type"] == "bar"
        assert visualization["recharts_component"] == "BarChart"


@pytest.mark.asyncio
async def test_visualization_agent_empty_results():
    """Test Visualization Agent with empty results."""
    agent = VisualizationAgent()
    
    query_understanding = {
        "intent": "Show products",
        "tables": ["products"],
        "columns": [],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    visualization = await agent.generate_visualization(
        query_understanding=query_understanding,
        natural_language_query="Show me products",
        sql="SELECT * FROM products WHERE id = 999;",
        results=[]
    )
    
    assert "chart_type" in visualization
    assert "title" in visualization
    assert "No Data Available" in visualization["title"] or "unavailable" in visualization["title"].lower()

