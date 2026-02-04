"""
Comprehensive tests for Analysis Agent.
Tests statistical insights, trend detection, anomaly detection, and recommendations.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.agents.analysis import AnalysisAgent
from app.core.redis_client import cache_service


@pytest.fixture
def analysis_agent():
    """Create an AnalysisAgent instance for testing."""
    return AnalysisAgent()


@pytest.mark.asyncio
async def test_statistical_insights(analysis_agent):
    """Test statistical insights generation (mean, median, mode, std dev)."""
    query_understanding = {
        "intent": "Analyze product prices",
        "tables": ["products"],
        "columns": ["price"],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    results = [
        {"price": 100},
        {"price": 200},
        {"price": 300},
        {"price": 150},
        {"price": 250}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": [
                "Average price is $200",
                "Price range is $100-$300",
                "Standard deviation is $75.59"
            ],
            "trends": [],
            "anomalies": [],
            "recommendations": ["Monitor price distribution"],
            "summary": "Product prices range from $100 to $300 with an average of $200."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Show me product prices",
            sql="SELECT price FROM products;",
            results=results
        )
        
        assert "insights" in analysis
        assert len(analysis["insights"]) > 0
        assert "summary" in analysis
        assert "recommendations" in analysis


@pytest.mark.asyncio
async def test_trend_detection_time_series(analysis_agent):
    """Test trend detection in time-series data."""
    query_understanding = {
        "intent": "Analyze sales over time",
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
        {"month": "2024-03", "total_sales": 15000},
        {"month": "2024-04", "total_sales": 18000}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": ["Sales are increasing month-over-month"],
            "trends": [
                {
                    "type": "increasing",
                    "description": "Sales show consistent growth from $10K to $18K",
                    "period": "month-over-month"
                }
            ],
            "anomalies": [],
            "recommendations": ["Continue current sales strategy"],
            "summary": "Sales are trending upward with consistent growth."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Show me sales by month",
            sql="SELECT DATE_TRUNC('month', order_date) as month, SUM(total_amount) as total_sales FROM sales_orders GROUP BY month;",
            results=results
        )
        
        assert "trends" in analysis
        assert len(analysis["trends"]) > 0
        assert any("increasing" in str(t).lower() or t.get("type") == "increasing" for t in analysis["trends"])


@pytest.mark.asyncio
async def test_anomaly_detection(analysis_agent):
    """Test anomaly detection in data."""
    query_understanding = {
        "intent": "Analyze order amounts",
        "tables": ["sales_orders"],
        "columns": ["total_amount"],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    results = [
        {"total_amount": 100},
        {"total_amount": 150},
        {"total_amount": 200},
        {"total_amount": 50000},  # Anomaly
        {"total_amount": 180}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": ["One order has unusually high amount"],
            "trends": [],
            "anomalies": [
                {
                    "type": "outlier",
                    "description": "Order with amount $50,000 is significantly higher than average",
                    "value": 50000
                }
            ],
            "recommendations": ["Investigate the high-value order"],
            "summary": "Most orders are in the $100-$200 range, with one outlier at $50,000."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Show me order amounts",
            sql="SELECT total_amount FROM sales_orders;",
            results=results
        )
        
        assert "anomalies" in analysis
        assert len(analysis["anomalies"]) > 0


@pytest.mark.asyncio
async def test_correlation_discovery(analysis_agent):
    """Test correlation discovery between variables."""
    query_understanding = {
        "intent": "Analyze relationship between variables",
        "tables": ["products", "sales_order_items"],
        "columns": ["price", "quantity_sold"],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    results = [
        {"price": 10, "quantity_sold": 100},
        {"price": 20, "quantity_sold": 80},
        {"price": 30, "quantity_sold": 60},
        {"price": 40, "quantity_sold": 40}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": [
                "Negative correlation between price and quantity sold",
                "Higher prices result in lower sales volume"
            ],
            "trends": [],
            "anomalies": [],
            "recommendations": [
                "Consider price optimization strategy",
                "Balance price and volume for maximum revenue"
            ],
            "summary": "Data shows inverse relationship between price and sales quantity."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Show me price vs quantity sold",
            sql="SELECT price, quantity_sold FROM products p JOIN sales_order_items soi ON p.id = soi.product_id;",
            results=results
        )
        
        assert "insights" in analysis
        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) > 0


@pytest.mark.asyncio
async def test_recommendations_generation(analysis_agent):
    """Test actionable recommendations generation."""
    query_understanding = {
        "intent": "Analyze customer retention",
        "tables": ["customers"],
        "columns": ["last_order_date"],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    results = [
        {"customer_id": 1, "last_order_date": "2024-01-15"},
        {"customer_id": 2, "last_order_date": "2023-12-01"},
        {"customer_id": 3, "last_order_date": "2023-11-10"}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": ["Some customers haven't ordered recently"],
            "trends": [],
            "anomalies": [],
            "recommendations": [
                "Send re-engagement emails to inactive customers",
                "Offer special discounts to customers who haven't ordered in 60+ days"
            ],
            "summary": "Customer retention analysis shows some customers need re-engagement."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Show me customer last order dates",
            sql="SELECT customer_id, last_order_date FROM customers;",
            results=results
        )
        
        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) > 0
        assert all(isinstance(rec, str) for rec in analysis["recommendations"])


@pytest.mark.asyncio
async def test_empty_results_analysis(analysis_agent):
    """Test analysis with empty results."""
    query_understanding = {
        "intent": "Find customers",
        "tables": ["customers"],
        "columns": [],
        "filters": [],
        "aggregations": [],
        "group_by": [],
        "order_by": None
    }
    
    analysis = await analysis_agent.analyze_results(
        query_understanding=query_understanding,
        natural_language_query="Show me customers",
        sql="SELECT * FROM customers WHERE id = 999;",
        results=[]
    )
    
    assert "insights" in analysis
    assert "anomalies" in analysis
    assert len(analysis["anomalies"]) > 0 or "No results" in str(analysis["insights"]).lower() or "zero results" in str(analysis.get("summary", "")).lower()


@pytest.mark.asyncio
async def test_year_over_year_comparison(analysis_agent):
    """Test year-over-year trend comparison."""
    query_understanding = {
        "intent": "Compare sales year over year",
        "tables": ["sales_orders"],
        "columns": ["order_date", "total_amount"],
        "filters": [],
        "aggregations": ["SUM"],
        "group_by": ["year"],
        "order_by": None
    }
    
    results = [
        {"year": 2023, "total_sales": 100000},
        {"year": 2024, "total_sales": 120000}
    ]
    
    with patch.object(cache_service, 'get', new_callable=AsyncMock, return_value=None), \
         patch.object(cache_service, 'set', new_callable=AsyncMock), \
         patch.object(analysis_agent.llm, 'generate_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps({
            "insights": ["Sales increased 20% year-over-year"],
            "trends": [
                {
                    "type": "increasing",
                    "description": "20% growth from 2023 to 2024",
                    "period": "year-over-year"
                }
            ],
            "anomalies": [],
            "recommendations": ["Maintain growth trajectory"],
            "summary": "Sales show strong year-over-year growth of 20%."
        })
        
        analysis = await analysis_agent.analyze_results(
            query_understanding=query_understanding,
            natural_language_query="Compare sales by year",
            sql="SELECT EXTRACT(YEAR FROM order_date) as year, SUM(total_amount) as total_sales FROM sales_orders GROUP BY year;",
            results=results
        )
        
        assert "trends" in analysis
        assert any("year" in str(t).lower() or t.get("period") == "year-over-year" for t in analysis["trends"])

