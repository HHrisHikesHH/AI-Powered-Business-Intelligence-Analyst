"""
Query executor service.
Handles SQL execution with timeouts and row limits (Week 2).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
from typing import Dict, List, Any
import asyncio
from datetime import datetime, date
from decimal import Decimal
from app.core.config import settings


def _json_serialize_value(value: Any) -> Any:
    """
    Convert non-JSON-serializable values to JSON-serializable types.
    
    Args:
        value: Value to convert
    
    Returns:
        JSON-serializable value
    """
    if value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        # Convert Decimal to float for JSON serialization
        # Use float() to preserve numeric type, or str() if precision is critical
        return float(value)
    elif isinstance(value, (list, tuple)):
        return [_json_serialize_value(item) for item in value]
    elif isinstance(value, dict):
        return {k: _json_serialize_value(v) for k, v in value.items()}
    else:
        return value


class QueryExecutor:
    """Service for executing SQL queries with safety measures."""
    
    # Default timeout in seconds
    DEFAULT_TIMEOUT = 30
    
    # Default row limit
    DEFAULT_ROW_LIMIT = 10000
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _execute_sql(
        self,
        sql: str,
        timeout: int = None,
        row_limit: int = None
    ) -> List[Dict]:
        """
        Execute SQL query against database with timeout and row limits.
        
        Args:
            sql: SQL query string
            timeout: Query timeout in seconds (default: 30)
            row_limit: Maximum rows to return (default: 10000)
        
        Returns:
            List of result dictionaries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        row_limit = row_limit or self.DEFAULT_ROW_LIMIT
        
        try:
            # Basic validation - only allow SELECT statements
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Add LIMIT if not present (safety measure)
            # But be careful - don't add LIMIT if there's already one or if it's an aggregation without GROUP BY
            if "LIMIT" not in sql_upper:
                # Remove trailing semicolon if present
                sql_clean = sql.rstrip(';').strip()
                # Only add LIMIT if it's not an aggregation query (those return single row anyway)
                # Check if it's a simple aggregation
                has_aggregation = any(func in sql_upper for func in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("])
                has_group_by = "GROUP BY" in sql_upper
                
                # Add LIMIT for non-aggregation queries or GROUP BY queries
                if not has_aggregation or has_group_by:
                    sql = f"{sql_clean} LIMIT {row_limit}"
                else:
                    sql = sql_clean
            
            # Rollback any previous failed transaction to ensure clean state
            try:
                await self.db.rollback()
            except:
                pass
            
            # Execute query with timeout
            # Use autocommit for SELECT queries to avoid transaction issues
            try:
                # For asyncpg, we need to use connection directly for autocommit
                # But SQLAlchemy async doesn't support autocommit easily
                # So we'll ensure we're in a clean transaction state
                result = await asyncio.wait_for(
                    self.db.execute(text(sql)),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    await self.db.rollback()
                except:
                    pass
                raise ValueError(f"Query timeout after {timeout} seconds")
            
            rows = result.fetchall()
            
            # Convert to list of dicts with JSON-serializable values
            columns = result.keys()
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # Convert non-JSON-serializable types (datetime, Decimal, etc.)
                serialized_dict = {k: _json_serialize_value(v) for k, v in row_dict.items()}
                results.append(serialized_dict)
            
            # For SELECT queries, we don't need to commit, but we should rollback
            # to ensure clean state for next query
            try:
                await self.db.rollback()  # Rollback SELECT to clean transaction state
            except:
                pass
            
            # Enforce row limit (in case LIMIT wasn't applied)
            if len(results) > row_limit:
                logger.warning(f"Query returned {len(results)} rows, limiting to {row_limit}")
                results = results[:row_limit]
            
            logger.info(f"Query returned {len(results)} rows")
            return results
            
        except asyncio.TimeoutError:
            logger.error(f"Query timeout after {timeout} seconds")
            try:
                await self.db.rollback()
            except:
                pass
            raise ValueError(f"Query timeout after {timeout} seconds")
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            # Rollback on error
            try:
                await self.db.rollback()
            except:
                pass
            raise ValueError(f"SQL execution failed: {e}")

