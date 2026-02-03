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
            
            # Filter out tokens that don't match known tables (likely aliases)
            valid_tables = []
            for table in tables:
                if table in self._schema_cache:
                    valid_tables.append(table)
                else:
                    # Treat unknown identifiers here as potential aliases rather than hard errors
                    logger.debug(f"Ignoring unknown table/alias '{table}' during schema validation")
            
            if not valid_tables:
                return False, "No valid tables found in SQL for schema validation"
            
            tables = valid_tables
            
            # Extract column references (simplified - doesn't handle all cases)
            # This is a basic check; full column validation would require parsing JOINs
            columns = self._extract_column_references(sql, tables)
            
            # Validate columns exist in their respective tables
            for table, column in columns:
                if table in self._schema_cache:
                    if column not in self._schema_cache[table]:
                        # Allow * as it's valid
                        if column != "*":
                            # Build user-friendly error message with available columns
                            available_cols = self._schema_cache[table]
                            available_cols_str = ", ".join(sorted(available_cols))
                            return False, (
                                f"Column '{column}' does not exist in table '{table}'. "
                                f"Available columns in '{table}': {available_cols_str}. "
                                f"Please reformulate your query using only the available columns."
                            )
            
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
        Handles both table.column and bare column references.
        
        Args:
            sql: SQL query string
            tables: List of table names
        
        Returns:
            List of (table, column) tuples
        """
        columns = []
        sql_lower = sql.lower()
        
        # Extract table.column patterns
        for table in tables:
            pattern = rf'\b{table}\.(\w+)\b'
            matches = re.findall(pattern, sql_lower)
            for match in matches:
                columns.append((table, match))
        
        # Extract bare column references from WHERE, SELECT, GROUP BY, ORDER BY, HAVING
        # This is more complex - we need to avoid keywords and function calls
        # Common SQL keywords to exclude
        sql_keywords = {
            'select', 'from', 'where', 'group', 'by', 'order', 'having', 'limit', 'offset',
            'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null', 'as', 'count', 'sum',
            'avg', 'max', 'min', 'distinct', 'case', 'when', 'then', 'else', 'end'
        }
        
        # Extract columns from WHERE clause
        where_pattern = r'\bwhere\s+(.+?)(?:\s+group\s+by|\s+order\s+by|\s+having|\s+limit|$)'
        where_match = re.search(where_pattern, sql_lower, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            
            # Remove string literals (single and double quoted) to avoid treating them as column names
            # This handles: WHERE country = 'USA', WHERE name = "John", etc.
            where_clause = re.sub(r"'[^']*'", '', where_clause)  # Remove single-quoted strings
            where_clause = re.sub(r'"[^"]*"', '', where_clause)  # Remove double-quoted strings
            
            # Remove numeric literals
            where_clause = re.sub(r'\b\d+\.?\d*\b', '', where_clause)
            
            # Extract identifiers that aren't keywords, strings, or numbers
            identifiers = re.findall(r'\b([a-z_][a-z0-9_]*)\b', where_clause)
            for identifier in identifiers:
                if identifier not in sql_keywords and identifier not in [t.lower() for t in tables]:
                    # Check if it's a column in any of the tables
                    for table in tables:
                        if identifier in [col.lower() for col in self._schema_cache.get(table, [])]:
                            columns.append((table, identifier))
                            break
                    else:
                        # Column not found in any table - add with first table as context
                        if tables:
                            columns.append((tables[0], identifier))
        
        # Extract columns from SELECT clause (e.g., "SELECT name, email")
        # IMPORTANT: We should NOT extract aliases (anything after AS keyword)
        select_pattern = r'\bselect\s+(.+?)\s+from'
        select_match = re.search(select_pattern, sql_lower, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            
            # Split by comma to handle multiple SELECT items
            select_items = [item.strip() for item in select_clause.split(',')]
            
            for item in select_items:
                # Remove aliases first (everything after AS keyword, including the AS and alias name)
                # This handles: "COUNT(*) AS customer_count", "name AS customer_name", etc.
                item = re.sub(r'\s+as\s+\w+.*$', '', item, flags=re.IGNORECASE)
                
                # Extract columns from within aggregation functions (e.g., COUNT(column_name))
                function_pattern = r'\b(count|sum|avg|max|min|distinct)\s*\(\s*([^)]+)\s*\)'
                function_matches = re.finditer(function_pattern, item, re.IGNORECASE)
                for match in function_matches:
                    func_arg = match.group(2).strip()
                    # If it's not * and not a number, it might be a column
                    if func_arg != '*' and not func_arg.replace('.', '').isdigit():
                        # Check if it's a column reference
                        for table in tables:
                            if func_arg.lower() in [col.lower() for col in self._schema_cache.get(table, [])]:
                                columns.append((table, func_arg.lower()))
                                break
                
                # Remove all function calls and aggregations for remaining extraction
                item = re.sub(r'\w+\s*\([^)]*\)', '', item)
                
                # Extract identifiers that might be columns (but not aliases)
                # Only extract if they look like actual column references
                identifiers = re.findall(r'\b([a-z_][a-z0-9_]*)\b', item)
                for identifier in identifiers:
                    if identifier not in sql_keywords and identifier != '*':
                        # Check if it's a column in any of the tables
                        for table in tables:
                            if identifier in [col.lower() for col in self._schema_cache.get(table, [])]:
                                columns.append((table, identifier))
                                break
                        # Don't add to columns if not found - it might be an alias or function result
        
        # Extract columns from GROUP BY and ORDER BY
        for clause_type in ['group by', 'order by']:
            pattern = rf'\b{clause_type}\s+([^\s]+(?:\s*,\s*[^\s]+)*)'
            match = re.search(pattern, sql_lower, re.IGNORECASE)
            if match:
                clause_columns = [col.strip() for col in match.group(1).split(',')]
                for col in clause_columns:
                    # Remove ASC/DESC
                    col = re.sub(r'\s+(asc|desc)$', '', col, flags=re.IGNORECASE).strip()
                    if col and col not in sql_keywords:
                        for table in tables:
                            if col in [c.lower() for c in self._schema_cache.get(table, [])]:
                                columns.append((table, col))
                                break
                        else:
                            if tables:
                                columns.append((tables[0], col))
        
        return columns

