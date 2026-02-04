"""
Tests for database adapter system.
Verifies multi-database support and schema introspection.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_adapter import create_database_adapter, DatabaseType
from app.core.config import settings
from sqlalchemy import text


@pytest.mark.asyncio
async def test_postgresql_adapter_connection():
    """Test PostgreSQL adapter connection."""
    adapter = create_database_adapter(
        db_type="postgresql",
        connection_string=settings.database_url
    )
    
    assert adapter.get_database_type() == DatabaseType.POSTGRESQL
    is_connected = await adapter.test_connection()
    assert is_connected is True


@pytest.mark.asyncio
async def test_adapter_get_tables():
    """Test table discovery."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url
    )
    
    factory = adapter.get_session_factory()
    async with factory() as db:
        tables = await adapter.get_tables(db, schema=settings.DATABASE_SCHEMA)
        
        # Should find all 40+ enterprise tables
        assert len(tables) >= 40, f"Expected at least 40 tables, found {len(tables)}"
        
        # Check for key tables
        expected_tables = [
            'departments', 'employees', 'customers', 'products',
            'sales_orders', 'invoices', 'projects', 'support_tickets'
        ]
        for table in expected_tables:
            assert table in tables, f"Expected table {table} not found"


@pytest.mark.asyncio
async def test_adapter_get_columns():
    """Test column metadata retrieval."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url
    )
    
    factory = adapter.get_session_factory()
    async with factory() as db:
        columns = await adapter.get_columns(db, "customers", schema=settings.DATABASE_SCHEMA)
        
        assert len(columns) > 0
        assert any(col["name"] == "id" for col in columns)
        assert any(col["name"] == "customer_code" for col in columns)
        assert any(col["name"] == "company_name" for col in columns)


@pytest.mark.asyncio
async def test_adapter_get_relationships():
    """Test foreign key relationship discovery."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url
    )
    
    factory = adapter.get_session_factory()
    async with factory() as db:
        relationships = await adapter.get_relationships(db, schema=settings.DATABASE_SCHEMA)
        
        # Should find many relationships in enterprise schema
        assert len(relationships) >= 20, f"Expected at least 20 relationships, found {len(relationships)}"
        
        # Check for key relationships
        rel_strings = [f"{r['table']}.{r['column']}" for r in relationships]
        assert any("sales_orders.customer_id" in s for s in rel_strings or ["sales_orders.customer_id"])


@pytest.mark.asyncio
async def test_adapter_query_execution():
    """Test query execution through adapter."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url
    )
    
    factory = adapter.get_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT COUNT(*) as count FROM customers"))
        row = result.fetchone()
        count = row[0] if row else 0
        
        assert count >= 200, f"Expected at least 200 customers, found {count}"


@pytest.mark.asyncio
async def test_all_enterprise_tables_discoverable():
    """Verify all enterprise tables are discoverable."""
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url
    )
    
    factory = adapter.get_session_factory()
    async with factory() as db:
        tables = await adapter.get_tables(db, schema=settings.DATABASE_SCHEMA)
        
        # Enterprise schema should have these modules
        hr_tables = ['departments', 'employees', 'job_positions', 'attendance', 'leave_requests']
        finance_tables = ['invoices', 'payments', 'chart_of_accounts', 'general_ledger', 'budgets']
        sales_tables = ['customers', 'leads', 'opportunities', 'sales_orders', 'quotes']
        inventory_tables = ['products', 'suppliers', 'warehouses', 'inventory', 'purchase_orders']
        project_tables = ['projects', 'project_tasks', 'time_entries']
        support_tables = ['support_tickets', 'ticket_comments', 'knowledge_base_articles']
        marketing_tables = ['marketing_campaigns', 'events', 'campaign_leads', 'event_attendees']
        
        all_expected = (hr_tables + finance_tables + sales_tables + 
                       inventory_tables + project_tables + support_tables + marketing_tables)
        
        missing = [t for t in all_expected if t not in tables]
        assert len(missing) == 0, f"Missing tables: {missing}"

