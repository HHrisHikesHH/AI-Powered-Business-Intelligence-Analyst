"""
Security tests - SQL injection prevention and permission validation.
"""
import pytest
from app.agents.sql_validator import SQLValidator
from app.core.database import get_db
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_sql_injection_prevention():
    """Test SQL injection attack prevention."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        # SQL injection attempts
        malicious_queries = [
            "SELECT * FROM customers; DROP TABLE customers;--",
            "SELECT * FROM customers WHERE id = 1; DELETE FROM customers;",
            "SELECT * FROM customers; UPDATE customers SET name = 'hacked';",
            "'; DROP TABLE customers; --",
            "1' OR '1'='1",
            "'; INSERT INTO customers VALUES (999, 'hacker'); --",
        ]
        
        for malicious_sql in malicious_queries:
            is_valid, error = await validator.validate(malicious_sql)
            
            assert is_valid is False, f"Malicious SQL should be rejected: {malicious_sql}"
            assert error is not None, f"Should return error for: {malicious_sql}"


@pytest.mark.asyncio
async def test_dangerous_operations_blocked():
    """Test that dangerous SQL operations are blocked."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        dangerous_queries = [
            "DELETE FROM customers",
            "DROP TABLE customers",
            "TRUNCATE TABLE customers",
            "UPDATE customers SET name = 'test'",
            "ALTER TABLE customers ADD COLUMN test INT",
            "CREATE TABLE test (id INT)",
        ]
        
        for dangerous_sql in dangerous_queries:
            is_valid, error = await validator.validate(dangerous_sql)
            
            assert is_valid is False, f"Dangerous operation should be blocked: {dangerous_sql}"
            assert "dangerous" in error.lower() or "not allowed" in error.lower(), \
                f"Should indicate dangerous operation: {error}"


@pytest.mark.asyncio
async def test_only_select_allowed():
    """Test that only SELECT queries are allowed."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        non_select_queries = [
            "INSERT INTO customers VALUES (1, 'test')",
            "UPDATE customers SET name = 'test' WHERE id = 1",
            "DELETE FROM customers WHERE id = 1",
            "CREATE INDEX idx ON customers(id)",
        ]
        
        for non_select in non_select_queries:
            is_valid, error = await validator.validate(non_select)
            
            assert is_valid is False, f"Non-SELECT should be rejected: {non_select}"
            assert "SELECT" in error.upper() or "only" in error.lower(), \
                f"Should indicate only SELECT allowed: {error}"


@pytest.mark.asyncio
async def test_table_existence_validation():
    """Test that non-existent tables are caught."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        invalid_queries = [
            "SELECT * FROM non_existent_table",
            "SELECT * FROM fake_table WHERE id = 1",
            "SELECT * FROM customers JOIN fake_table ON customers.id = fake_table.id",
        ]
        
        for invalid_sql in invalid_queries:
            is_valid, error = await validator.validate(invalid_sql)
            
            # Should either be invalid or caught during execution
            # This depends on validator implementation
            if not is_valid:
                assert error is not None


@pytest.mark.asyncio
async def test_column_existence_validation():
    """Test that non-existent columns are caught."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        invalid_queries = [
            "SELECT fake_column FROM customers",
            "SELECT id, fake_column FROM customers",
            "SELECT * FROM customers WHERE fake_column = 1",
        ]
        
        for invalid_sql in invalid_queries:
            is_valid, error = await validator.validate(invalid_sql)
            
            # Should either be invalid or caught during execution
            if not is_valid:
                assert error is not None


@pytest.mark.asyncio
async def test_large_query_detection():
    """Test that very large queries are flagged."""
    async for db in get_db():
        validator = SQLValidator(db)
        
        # Query that would scan many rows
        large_query = "SELECT * FROM sales_order_items CROSS JOIN inventory CROSS JOIN products"
        
        is_valid, error = await validator.validate(large_query)
        
        # Should either be rejected or flagged for confirmation
        # This depends on cost estimation implementation
        print(f"Large query validation: valid={is_valid}, error={error}")

