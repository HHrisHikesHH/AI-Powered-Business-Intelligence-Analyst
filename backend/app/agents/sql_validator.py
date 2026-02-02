"""
SQL Validation Module.
Validates SQL syntax and checks table/column existence.
"""
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML
from loguru import logger
from typing import Dict, List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
import re


class SQLValidator:
    """Validates SQL queries for syntax, safety, and schema correctness."""
    
    # Dangerous operations that should be blocked
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"
    }
    
    # Allowed operations
    ALLOWED_DML = {"SELECT"}
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._schema_cache: Optional[Dict[str, List[str]]] = None
    
    async def validate(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query.
        
        Args:
            sql: SQL query string
        
        Returns:
            Tuple of (is_valid, error_message)
            If is_valid is True, error_message is None
            If is_valid is False, error_message contains the reason
        """
        try:
            # Step 1: Syntax validation
            is_valid, error = self._validate_syntax(sql)
            if not is_valid:
                return False, error
            
            # Step 2: Safety validation (dangerous operations)
            is_valid, error = self._validate_safety(sql)
            if not is_valid:
                return False, error
            
            # Step 3: Schema validation (table/column existence)
            is_valid, error = await self._validate_schema(sql)
            if not is_valid:
                return False, error
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error during SQL validation: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_syntax(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL syntax using sqlparse.
        
        Args:
            sql: SQL query string
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql)
            
            if not parsed:
                return False, "Empty or invalid SQL statement"
            
            # Check for multiple statements (should only have one)
            if len(parsed) > 1:
                return False, "Multiple SQL statements not allowed"
            
            statement = parsed[0]
            
            # Check if it's a valid statement
            if not statement.tokens:
                return False, "Invalid SQL syntax"
            
            return True, None
            
        except Exception as e:
            logger.error(f"SQL syntax validation error: {e}")
            return False, f"SQL syntax error: {str(e)}"
    
    def _validate_safety(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that SQL doesn't contain dangerous operations.
        
        Args:
            sql: SQL query string
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        sql_upper = sql.upper()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Dangerous operation detected: {keyword}. Only SELECT queries are allowed."
        
        # Ensure it's a SELECT statement
        if not sql_upper.strip().startswith("SELECT"):
            return False, "Only SELECT queries are allowed"
        
        # Check for UPDATE/DELETE without WHERE (if somehow they got through)
        if "UPDATE" in sql_upper and "WHERE" not in sql_upper:
            return False, "UPDATE without WHERE clause is not allowed"
        
        if "DELETE" in sql_upper and "WHERE" not in sql_upper:
            return False, "DELETE without WHERE clause is not allowed"
        
        return True, None
    
    async def _validate_schema(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that tables and columns exist in the database.
        
        Args:
            sql: SQL query string
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Load schema cache if not loaded
            if self._schema_cache is None:
                await self._load_schema_cache()
            
            # Extract table names from SQL
            tables = self._extract_tables(sql)
            
            # Validate tables exist
            for table in tables:
                if table not in self._schema_cache:
                    return False, f"Table '{table}' does not exist"
            
            # Extract column references (simplified - doesn't handle all cases)
            # This is a basic check; full column validation would require parsing JOINs
            columns = self._extract_column_references(sql, tables)
            
            # Validate columns exist in their respective tables
            for table, column in columns:
                if table in self._schema_cache:
                    if column not in self._schema_cache[table]:
                        # Allow * as it's valid
                        if column != "*":
                            return False, f"Column '{column}' does not exist in table '{table}'"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            # Don't fail validation on schema cache errors - allow query to proceed
            # but log the error
            return True, None
    
    async def _load_schema_cache(self):
        """Load database schema into cache."""
        try:
            # Query information_schema to get tables and columns
            result = await self.db.execute(text("""
                SELECT 
                    table_name,
                    column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """))
            
            rows = result.fetchall()
            
            # Build schema cache
            self._schema_cache = {}
            for row in rows:
                table_name = row[0]
                column_name = row[1]
                
                if table_name not in self._schema_cache:
                    self._schema_cache[table_name] = []
                self._schema_cache[table_name].append(column_name)
            
            logger.info(f"Loaded schema cache with {len(self._schema_cache)} tables")
            
        except Exception as e:
            logger.error(f"Error loading schema cache: {e}")
            self._schema_cache = {}
    
    def _extract_tables(self, sql: str) -> List[str]:
        """
        Extract table names from SQL query.
        Simplified extraction - doesn't handle all edge cases.
        
        Args:
            sql: SQL query string
        
        Returns:
            List of table names
        """
        tables = []
        sql_upper = sql.upper()
        
        # Simple regex to find FROM and JOIN clauses
        # FROM table_name
        from_matches = re.findall(r'\bFROM\s+(\w+)', sql_upper)
        tables.extend(from_matches)
        
        # JOIN table_name
        join_matches = re.findall(r'\bJOIN\s+(\w+)', sql_upper)
        tables.extend(join_matches)
        
        # Remove duplicates and normalize
        tables = list(set([t.lower() for t in tables]))
        
        return tables
    
    def _extract_column_references(self, sql: str, tables: List[str]) -> List[Tuple[str, str]]:
        """
        Extract column references from SQL.
        Simplified - only handles basic cases.
        
        Args:
            sql: SQL query string
            tables: List of table names
        
        Returns:
            List of (table, column) tuples
        """
        columns = []
        
        # This is a simplified extraction
        # For each table, look for table.column patterns
        for table in tables:
            pattern = rf'\b{table}\.(\w+)\b'
            matches = re.findall(pattern, sql.lower())
            for match in matches:
                columns.append((table, match))
        
        return columns

