"""
Query executor service.
Handles SQL generation and execution (simplified for Week 1).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
from app.core.llm_client import llm_service
from typing import Dict, List, Any
import json


class QueryExecutor:
    """Service for executing natural language queries."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = llm_service
    
    async def execute_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Execute natural language query.
        
        For Week 1, this is a simplified version that:
        1. Generates SQL using LLM
        2. Executes SQL against database
        3. Returns results
        
        Full multi-agent pipeline will be implemented in later phases.
        """
        try:
            # Step 1: Generate SQL from natural language
            sql = await self._generate_sql(natural_language_query)
            
            # Step 2: Execute SQL
            results = await self._execute_sql(sql)
            
            return {
                "sql": sql,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    async def _generate_sql(self, query: str) -> str:
        """Generate SQL from natural language query using LLM."""
        system_prompt = """You are a SQL expert. Generate PostgreSQL SQL queries from natural language questions.
        
Available tables:
- customers (id, name, email, created_at, city, country)
- products (id, name, category, price, stock_quantity)
- orders (id, customer_id, order_date, total_amount, status)
- order_items (id, order_id, product_id, quantity, line_total)

Rules:
1. Only generate SELECT queries
2. Use proper JOINs when needed
3. Include appropriate WHERE clauses
4. Use LIMIT 100 if not specified
5. Return only the SQL query, no explanations"""

        prompt = f"Convert this natural language query to PostgreSQL SQL:\n\n{query}"
        
        try:
            sql = await self.llm.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Clean up SQL (remove markdown code blocks if present)
            sql = sql.strip()
            if sql.startswith("```sql"):
                sql = sql[6:]
            elif sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            
            logger.info(f"Generated SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise ValueError(f"Failed to generate SQL: {e}")
    
    async def _execute_sql(self, sql: str) -> List[Dict]:
        """Execute SQL query against database."""
        try:
            # Basic validation - only allow SELECT statements
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Add LIMIT if not present (safety measure)
            if "LIMIT" not in sql_upper:
                sql = f"{sql.rstrip(';')} LIMIT 10000"
            
            # Execute query
            result = await self.db.execute(text(sql))
            rows = result.fetchall()
            
            # Convert to list of dicts
            columns = result.keys()
            results = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"Query returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise ValueError(f"SQL execution failed: {e}")

