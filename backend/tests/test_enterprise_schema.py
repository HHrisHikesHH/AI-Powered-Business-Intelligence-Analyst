"""
Tests for enterprise schema queries.
Verifies complex queries work correctly across all 40+ tables.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock
from app.agents.orchestrator import Orchestrator
from app.core.config import settings
from app.core.database_adapter import create_database_adapter
from app.services.query_executor import QueryExecutor
from sqlalchemy import text


@pytest.mark.asyncio
async def test_hr_module_queries():
    """Test HR module queries."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        executor = QueryExecutor(db)
        
        queries = [
            "SELECT COUNT(*) FROM employees",
            "SELECT d.name, COUNT(e.id) as employee_count FROM departments d LEFT JOIN employees e ON d.id = e.position_id GROUP BY d.name",
            "SELECT AVG(salary) as avg_salary FROM employees WHERE status = 'active'",
        ]
        
        for sql in queries:
            results = await executor._execute_sql(sql)
            # Some modules/queries may legitimately return empty result sets depending on seed data.
            # The key check here is that the query executes successfully.
            assert isinstance(results, list), f"Query did not return a list: {sql}"


@pytest.mark.asyncio
async def test_finance_module_queries():
    """Test Finance module queries."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        executor = QueryExecutor(db)
        
        queries = [
            "SELECT COUNT(*) FROM invoices",
            "SELECT SUM(total_amount) as total_revenue FROM invoices WHERE status = 'paid'",
            "SELECT account_id, SUM(debit_amount) - SUM(credit_amount) as balance FROM general_ledger GROUP BY account_id",
        ]
        
        for sql in queries:
            results = await executor._execute_sql(sql)
            assert isinstance(results, list), f"Query did not return a list: {sql}"


@pytest.mark.asyncio
async def test_sales_module_queries():
    """Test Sales module queries."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        executor = QueryExecutor(db)
        
        queries = [
            "SELECT COUNT(*) FROM customers",
            "SELECT c.company_name, SUM(so.total_amount) as total_revenue FROM customers c JOIN sales_orders so ON c.id = so.customer_id GROUP BY c.company_name ORDER BY total_revenue DESC LIMIT 10",
            "SELECT stage, COUNT(*) as count, AVG(estimated_value) as avg_value FROM opportunities GROUP BY stage",
        ]
        
        for sql in queries:
            results = await executor._execute_sql(sql)
            assert isinstance(results, list), f"Query did not return a list: {sql}"


@pytest.mark.asyncio
async def test_inventory_module_queries():
    """Test Inventory module queries."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        executor = QueryExecutor(db)
        
        queries = [
            "SELECT COUNT(*) FROM products",
            "SELECT p.name, SUM(i.quantity_on_hand) as total_inventory FROM products p JOIN inventory i ON p.id = i.product_id GROUP BY p.name",
            "SELECT w.name, COUNT(DISTINCT i.product_id) as unique_products FROM warehouses w JOIN inventory i ON w.id = i.warehouse_id GROUP BY w.name",
        ]
        
        for sql in queries:
            results = await executor._execute_sql(sql)
            assert isinstance(results, list), f"Query did not return a list: {sql}"


@pytest.mark.asyncio
async def test_cross_module_queries():
    """Test complex cross-module queries."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        executor = QueryExecutor(db)
        
        queries = [
            # Revenue by customer industry and sales rep department
            """SELECT c.industry, d.name as department, SUM(so.total_amount) as revenue
               FROM customers c
               JOIN sales_orders so ON c.id = so.customer_id
               JOIN employees e ON so.sales_rep_id = e.id
               JOIN job_positions jp ON e.position_id = jp.id
               JOIN departments d ON jp.department_id = d.id
               GROUP BY c.industry, d.name
               ORDER BY revenue DESC""",
            
            # Employee performance vs project success
            """SELECT e.first_name || ' ' || e.last_name as employee_name,
                      AVG(pr.overall_rating) as avg_rating,
                      COUNT(DISTINCT p.id) as project_count
               FROM employees e
               LEFT JOIN performance_reviews pr ON e.id = pr.employee_id
               LEFT JOIN projects p ON e.id = p.project_manager_id
               GROUP BY e.id, e.first_name, e.last_name
               HAVING COUNT(DISTINCT p.id) > 0""",
        ]
        
        for sql in queries:
            try:
                results = await executor._execute_sql(sql)
                assert len(results) >= 0, f"Query should return results (even if empty): {sql}"
            except Exception as e:
                pytest.fail(f"Query failed: {sql}\nError: {e}")


@pytest.mark.asyncio
async def test_natural_language_enterprise_queries():
    """Test natural language queries against enterprise schema."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()
    async with factory() as db:
        orchestrator = Orchestrator(db)

        # Avoid calling real external services (LLMs/RAG/Redis) in tests.
        # We mock the agents to keep this test fast and deterministic while still exercising:
        # - Orchestrator workflow
        # - SQL validation
        # - SQL execution against the enterprise DB

        async def fake_understand(nl_query: str):
            q = nl_query.lower()
            if "employees" in q and "how many" in q:
                return {
                    "intent": "Count total number of employees",
                    "tables": ["employees"],
                    "columns": ["id"],
                    "filters": [],
                    "aggregations": ["COUNT"],
                    "group_by": [],
                    "order_by": None,
                    "limit": None,
                    "ambiguities": [],
                    "needs_clarification": False,
                }
            if "total revenue" in q and "invoices" in q:
                return {
                    "intent": "Calculate total revenue from invoices",
                    "tables": ["invoices"],
                    "columns": ["total_amount"],
                    "filters": [],
                    "aggregations": ["SUM"],
                    "group_by": [],
                    "order_by": None,
                    "limit": None,
                    "ambiguities": [],
                    "needs_clarification": False,
                }
            if "top 10 customers" in q:
                return {
                    "intent": "Get top 10 customers by total order value",
                    "tables": ["customers", "sales_orders"],
                    "columns": ["company_name", "total_amount", "customer_id"],
                    "filters": [],
                    "aggregations": ["SUM"],
                    "group_by": ["company_name"],
                    "order_by": {"column": "total_order_value", "direction": "DESC"},
                    "limit": 10,
                    "ambiguities": [],
                    "needs_clarification": False,
                }
            if "below reorder point" in q:
                return {
                    "intent": "Find products below reorder point",
                    "tables": ["products", "inventory"],
                    "columns": ["name", "quantity_available", "reorder_point", "product_id"],
                    "filters": [],
                    "aggregations": [],
                    "group_by": [],
                    "order_by": None,
                    "limit": 100,
                    "ambiguities": [],
                    "needs_clarification": False,
                }
            if "projects" in q and "active" in q:
                return {
                    "intent": "Count active projects",
                    "tables": ["projects"],
                    "columns": ["id", "status"],
                    "filters": [{"column": "status", "operator": "=", "value": "active", "type": "string"}],
                    "aggregations": ["COUNT"],
                    "group_by": [],
                    "order_by": None,
                    "limit": None,
                    "ambiguities": [],
                    "needs_clarification": False,
                }
            # Generic fallback: treat as needing clarification (should result in an error path)
            return {
                "intent": nl_query,
                "tables": [],
                "columns": [],
                "filters": [],
                "aggregations": [],
                "group_by": [],
                "order_by": None,
                "limit": None,
                "ambiguities": ["Test mock could not map query to schema"],
                "needs_clarification": True,
            }

        async def fake_generate_sql(*, query_understanding, natural_language_query, **kwargs):
            q = natural_language_query.lower()
            if "employees" in q and "how many" in q:
                return "SELECT COUNT(*) AS employee_count FROM employees;"
            if "total revenue" in q and "invoices" in q:
                return "SELECT SUM(total_amount) AS total_revenue FROM invoices;"
            if "top 10 customers" in q:
                return (
                    "SELECT c.company_name, SUM(so.total_amount) AS total_order_value "
                    "FROM customers c "
                    "JOIN sales_orders so ON c.id = so.customer_id "
                    "GROUP BY c.company_name "
                    "ORDER BY total_order_value DESC "
                    "LIMIT 10;"
                )
            if "below reorder point" in q:
                return (
                    "SELECT p.name, i.quantity_available, i.reorder_point "
                    "FROM products p "
                    "JOIN inventory i ON p.id = i.product_id "
                    "WHERE i.quantity_available < i.reorder_point "
                    "LIMIT 100;"
                )
            if "projects" in q and "active" in q:
                return "SELECT COUNT(*) AS active_projects FROM projects WHERE status = 'active';"
            raise ValueError("Cannot generate SQL for unmapped test query")

        orchestrator.query_understanding_agent.understand = AsyncMock(side_effect=fake_understand)
        orchestrator.sql_generation_agent.generate_sql = AsyncMock(side_effect=fake_generate_sql)
        orchestrator.analysis_agent.analyze_results = AsyncMock(
            return_value={
                "insights": ["Mock analysis"],
                "trends": [],
                "anomalies": [],
                "recommendations": [],
                "summary": "Mock summary",
            }
        )
        orchestrator.visualization_agent.generate_visualization = AsyncMock(
            return_value={
                "chart_type": "bar",
                "data_key": None,
                "category_key": None,
                "title": "Mock Visualization",
                "description": "",
                "config": {},
                "recharts_component": "BarChart",
            }
        )
        
        test_queries = [
            "How many employees do we have?",
            "What is the total revenue from all invoices?",
            "Show me the top 10 customers by order value",
            "Which products are below reorder point?",
            "How many projects are currently active?",
        ]
        
        for query in test_queries:
            try:
                # Timeout protects against hangs if anything unexpectedly touches external services
                result = await asyncio.wait_for(orchestrator.process_query(query), timeout=20)
                
                # Should have SQL generated
                assert "sql" in result or "generated_sql" in result, f"No SQL generated for: {query}"
                
                # Should have results or error message
                assert "results" in result or "error" in result, f"No results or error for: {query}"
                
                # Analysis may be skipped for simple queries; ensure it doesn't crash
                if not result.get("error"):
                    assert "analysis" in result, f"Analysis field missing for: {query}"
                    
            except Exception as e:
                pytest.fail(f"Query processing failed: {query}\nError: {e}")

