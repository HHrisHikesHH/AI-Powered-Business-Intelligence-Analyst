"""
Comprehensive tests for Visualization Agent.
Tests chart type selection, Recharts configuration, and edge cases.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.agents.visualization import VisualizationAgent
from app.core.redis_client import cache_service


@pytest.fixture
def visualization_agent():
    """Create a VisualizationAgent instance for testing."""
    return VisualizationAgent()


@pytest.mark.asyncio
async def test_time_series_line_chart(visualization_agent):
    """Test time-series data → Line/Area chart."""
    query_understanding = {
        "intent": "Show sales over time",
        "tables": ["sales_orders"],
        "columns": ["order_date", "total_amount"],
        "filters": [],
        "aggregations": ["SUM"],
        "group_by": ["order_date"],
        "order_by": {"column": "order_date", "direction": "ASC"}
    }
    
    results = [
        {"month": "2024-01", "total_sales": 10000},
        {"month": "2024-02", "total_sales": 12000},
        {"month": "2024-03", "total_sales": 15000}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "line",
            "data_key": "total_sales",
            "category_key": "month",
            "title": "Sales Over Time",
            "description": "Line chart showing sales trend",
            "x_axis_label": "Month",
            "y_axis_label": "Total Sales",
            "colors": ["#8884d8"],
            "config": {
                "width": 800,
                "height": 400
            }
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Show me sales by month",
            sql="SELECT DATE_TRUNC('month', order_date) as month, SUM(total_amount) as total_sales FROM sales_orders GROUP BY month;",
            results=results
        )
        
        assert visualization["chart_type"] == "line"
        assert visualization["recharts_component"] == "LineChart"
        assert "data_key" in visualization
        assert "category_key" in visualization


@pytest.mark.asyncio
async def test_categorical_bar_chart(visualization_agent):
    """Test categorical data → Bar chart."""
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
        {"category": "Clothing", "product_count": 5},
        {"category": "Books", "product_count": 8}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "bar",
            "data_key": "product_count",
            "category_key": "category",
            "title": "Products by Category",
            "description": "Bar chart showing product count by category",
            "x_axis_label": "Category",
            "y_axis_label": "Product Count",
            "colors": ["#8884d8", "#82ca9d", "#ffc658"],
            "config": {
                "width": 800,
                "height": 400
            }
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Show me products by category",
            sql="SELECT category, COUNT(*) as product_count FROM products GROUP BY category;",
            results=results
        )
        
        assert visualization["chart_type"] == "bar"
        assert visualization["recharts_component"] == "BarChart"
        assert visualization["data_key"] == "product_count"
        assert visualization["category_key"] == "category"


@pytest.mark.asyncio
async def test_single_value_number_card(visualization_agent):
    """Test single value → Number card."""
    query_understanding = {
        "intent": "Count total customers",
        "tables": ["customers"],
        "columns": ["id"],
        "filters": [],
        "aggregations": ["COUNT"],
        "group_by": [],
        "order_by": None
    }
    
    results = [{"customer_count": 150}]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "number",
            "data_key": "customer_count",
            "title": "Total Customers",
            "description": "Total number of customers",
            "value": 150,
            "config": {}
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="How many customers?",
            sql="SELECT COUNT(*) as customer_count FROM customers;",
            results=results
        )
        
        assert "chart_type" in visualization
        assert "title" in visualization


@pytest.mark.asyncio
async def test_comparison_bar_chart(visualization_agent):
    """Test comparison data → Bar chart."""
    query_understanding = {
        "intent": "Compare sales by region",
        "tables": ["sales_orders", "customers"],
        "columns": ["region", "total_amount"],
        "filters": [],
        "aggregations": ["SUM"],
        "group_by": ["region"],
        "order_by": None
    }
    
    results = [
        {"region": "North", "total_sales": 50000},
        {"region": "South", "total_sales": 45000},
        {"region": "East", "total_sales": 60000}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "bar",
            "data_key": "total_sales",
            "category_key": "region",
            "title": "Sales by Region",
            "description": "Bar chart comparing sales across regions",
            "x_axis_label": "Region",
            "y_axis_label": "Total Sales",
            "colors": ["#8884d8", "#82ca9d", "#ffc658"],
            "config": {
                "width": 800,
                "height": 400
            }
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Compare sales by region",
            sql="SELECT c.region, SUM(o.total_amount) as total_sales FROM customers c JOIN sales_orders o ON c.id = o.customer_id GROUP BY c.region;",
            results=results
        )
        
        assert visualization["chart_type"] == "bar"
        assert "data_key" in visualization
        assert "category_key" in visualization


@pytest.mark.asyncio
async def test_distribution_histogram(visualization_agent):
    """Test distribution data → Histogram."""
    query_understanding = {
        "intent": "Show price distribution",
        "tables": ["products"],
        "columns": ["price"],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    results = [
        {"price_range": "0-50", "count": 10},
        {"price_range": "50-100", "count": 25},
        {"price_range": "100-200", "count": 15}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "bar",
            "data_key": "count",
            "category_key": "price_range",
            "title": "Price Distribution",
            "description": "Histogram showing product price distribution",
            "x_axis_label": "Price Range",
            "y_axis_label": "Count",
            "colors": ["#8884d8"],
            "config": {
                "width": 800,
                "height": 400
            }
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Show me price distribution",
            sql="SELECT price_range, COUNT(*) as count FROM products GROUP BY price_range;",
            results=results
        )
        
        assert "chart_type" in visualization
        assert "data_key" in visualization


@pytest.mark.asyncio
async def test_empty_results_visualization(visualization_agent):
    """Test visualization with empty results."""
    query_understanding = {
        "intent": "Show products",
        "tables": ["products"],
        "columns": [],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    visualization = await visualization_agent.generate_visualization(
        query_understanding=query_understanding,
        natural_language_query="Show me products",
        sql="SELECT * FROM products WHERE id = 999;",
        results=[]
    )
    
    assert "chart_type" in visualization
    assert "title" in visualization
    assert "No Data" in visualization["title"] or "unavailable" in visualization["title"].lower()


@pytest.mark.asyncio
async def test_single_data_point(visualization_agent):
    """Test visualization with single data point."""
    query_understanding = {
        "intent": "Get single value",
        "tables": ["customers"],
        "columns": ["id"],
        "filters": [],
        "aggregations": ["COUNT"],
        "group_by": [],
        "order_by": None
    }
    
    results = [{"count": 1}]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "number",
            "data_key": "count",
            "title": "Count",
            "description": "Single value display",
            "value": 1,
            "config": {}
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Count",
            sql="SELECT COUNT(*) as count FROM customers;",
            results=results
        )
        
        assert "chart_type" in visualization
        assert "title" in visualization


@pytest.mark.asyncio
async def test_recharts_configuration(visualization_agent):
    """Test that Recharts configuration is valid."""
    query_understanding = {
        "intent": "Show data",
        "tables": ["products"],
        "columns": ["category", "count"],
        "filters": [],
        "aggregations": ["COUNT"],
        "group_by": ["category"],
        "order_by": None
    }
    
    results = [
        {"category": "A", "count": 10},
        {"category": "B", "count": 20}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(visualization_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "chart_type": "bar",
            "data_key": "count",
            "category_key": "category",
            "title": "Test Chart",
            "description": "Test",
            "x_axis_label": "Category",
            "y_axis_label": "Count",
            "colors": ["#8884d8"],
            "recharts_component": "BarChart",
            "config": {
                "width": 800,
                "height": 400,
                "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
            }
        })
        
        visualization = await visualization_agent.generate_visualization(
            query_understanding=query_understanding,
            natural_language_query="Show data",
            sql="SELECT category, COUNT(*) as count FROM products GROUP BY category;",
            results=results
        )
        
        assert "recharts_component" in visualization
        assert "config" in visualization
        assert "width" in visualization["config"]
        assert "height" in visualization["config"]

