"""
SQL Generation Agent.
Generates SQL queries based on query understanding and schema context.
Uses hybrid RAG (vector + keyword + graph-based) to retrieve relevant schema information.
Supports self-correction when errors are detected.
"""
from loguru import logger
from app.core.llm_client import llm_service, QueryComplexity
from app.core.pgvector_client import vector_store
from app.services.hybrid_rag import HybridRAG
from app.agents.prompts import format_sql_generation_prompt, SQL_GENERATION_FEW_SHOT_EXAMPLES
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
import json


class SQLGenerationAgent:
    """Agent responsible for generating SQL queries from natural language."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.llm = llm_service
        self.vector_store = vector_store
        self.db = db
        self.hybrid_rag = HybridRAG(db) if db else None
    
    async def generate_sql(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        use_rag: bool = True,
        previous_error: Optional[str] = None,
        previous_sql: Optional[str] = None
    ) -> str:
        """
        Generate SQL query from query understanding.
        
        Args:
            query_understanding: Output from Query Understanding Agent
            natural_language_query: Original natural language query
            use_rag: Whether to use RAG for schema retrieval
        
        Returns:
            Generated SQL query string
        """
        try:
            logger.info(f"Generating SQL for intent: {query_understanding['intent']}")
            
            # Retrieve schema context using hybrid RAG
            schema_context = ""
            if use_rag:
                if self.hybrid_rag:
                    # Use hybrid RAG (vector + keyword + graph-based)
                    rag_results = await self.hybrid_rag.search(
                        query=natural_language_query,
                        query_understanding=query_understanding,
                        n_results=10
                    )
                    schema_context = self.hybrid_rag.format_context(rag_results)
                else:
                    # Fallback to vector-only RAG
                    schema_context = await self._retrieve_schema_context(
                        query_understanding,
                        natural_language_query
                    )
            
            # If RAG didn't return enough context, add dynamic schema info
            if not schema_context or len(schema_context) < 50:
                schema_context = await self._get_dynamic_schema_info()
            
            # Add error context if this is a retry
            error_context = ""
            if previous_error and previous_sql:
                error_context = f"""
PREVIOUS ATTEMPT FAILED:
SQL: {previous_sql}
Error: {previous_error}

Please correct the SQL query based on the error above. Ensure:
1. All table and column names exist in the schema
2. SQL syntax is correct
3. The query matches the user's intent: {natural_language_query}
"""
            
            # Format prompt with context
            prompt = format_sql_generation_prompt(
                query_understanding=query_understanding,
                schema_context=schema_context,
                few_shot_examples=SQL_GENERATION_FEW_SHOT_EXAMPLES
            )
            
            # Add query understanding as context
            understanding_str = json.dumps(query_understanding, indent=2)
            full_prompt = f"""Query Understanding:
{understanding_str}

Original Query: {natural_language_query}

{error_context}

{prompt}"""
            
            # Determine model complexity based on query understanding
            complexity = self._determine_complexity(query_understanding)
            
            # Generate SQL with retry logic
            sql = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    response = await self.llm.generate_completion(
                        prompt=full_prompt,
                        system_prompt="""You are a SQL Generation Agent. Your ONLY job is to generate a valid PostgreSQL SELECT query.

CRITICAL RULES:
1. Return ONLY the SQL query - no explanations, no markdown, no code blocks
2. Start directly with SELECT
3. Use proper PostgreSQL syntax
4. Include all necessary clauses (FROM, WHERE, GROUP BY, ORDER BY, LIMIT)
5. End with semicolon

Example format:
SELECT * FROM customers LIMIT 100;

Do NOT include:
- Explanations
- Markdown code blocks (```sql)
- Comments
- Any text before or after the SQL

Just the SQL query, nothing else.""",
                        temperature=0.1,  # Very low temperature for deterministic SQL
                        max_tokens=800,
                        complexity=complexity,
                        auto_select_model=True
                    )
                    
                    # Check if response is valid
                    if response and response.strip():
                        sql = self._clean_sql(response)
                        
                        # Validate SQL is not empty and starts with SELECT
                        if sql and sql.strip().upper().startswith("SELECT"):
                            logger.info(f"Generated SQL: {sql}")
                            return sql
                        else:
                            logger.warning(f"Invalid SQL generated (attempt {attempt + 1}): {sql[:100] if sql else 'empty'}")
                    else:
                        logger.warning(f"Empty response from LLM (attempt {attempt + 1})")
                        
                except Exception as e:
                    logger.warning(f"Error generating SQL (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        raise
            
            # If all retries failed, try fallback generation
            if not sql or not sql.strip().upper().startswith("SELECT"):
                logger.warning("Primary SQL generation failed, attempting fallback")
                sql = await self._generate_fallback_sql(query_understanding, natural_language_query)
            
            if not sql or not sql.strip().upper().startswith("SELECT"):
                raise ValueError("Failed to generate valid SQL after all attempts")
            
            logger.info(f"Generated SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise ValueError(f"Failed to generate SQL: {e}")
    
    async def self_correct_sql(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        previous_sql: str,
        error_message: str
    ) -> str:
        """
        Self-correct SQL based on previous error.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original natural language query
            previous_sql: Previously generated SQL that failed
            error_message: Error message from validation or execution
        
        Returns:
            Corrected SQL query string
        """
        logger.info(f"Attempting self-correction for SQL: {previous_sql[:100]}...")
        logger.info(f"Error: {error_message}")
        
        # Generate SQL with error context
        return await self.generate_sql(
            query_understanding=query_understanding,
            natural_language_query=natural_language_query,
            use_rag=True,
            previous_error=error_message,
            previous_sql=previous_sql
        )
    
    async def _retrieve_schema_context(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str
    ) -> str:
        """
        Retrieve relevant schema context using RAG.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
        
        Returns:
            Formatted schema context string
        """
        try:
            # Build search query from understanding
            search_terms = []
            search_terms.extend(query_understanding.get("tables", []))
            search_terms.extend(query_understanding.get("columns", []))
            search_terms.append(natural_language_query)
            
            search_query = " ".join(search_terms)
            
            # Search for similar schema elements
            results = await self.vector_store.search_similar(
                search_query,
                n_results=5
            )
            
            if not results:
                logger.warning("No schema context found via RAG")
                return ""
            
            # Format results as context
            context_parts = []
            for result in results:
                metadata = result.get("metadata", {})
                doc = result.get("document", "")
                
                if metadata.get("type") == "table":
                    context_parts.append(f"Table: {metadata.get('name', 'unknown')}")
                    context_parts.append(f"Columns: {', '.join(metadata.get('columns', []))}")
                elif metadata.get("type") == "column":
                    context_parts.append(f"Column: {metadata.get('table', 'unknown')}.{metadata.get('name', 'unknown')}")
                    context_parts.append(f"Type: {metadata.get('data_type', 'unknown')}")
                else:
                    context_parts.append(doc)
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Error retrieving schema context: {e}")
            return ""
    
    async def _get_dynamic_schema_info(self) -> str:
        """
        Get schema information dynamically from the database.
        Falls back to empty string if database introspection fails.
        
        Returns:
            Formatted schema information string
        """
        if not self.db:
            logger.warning("No database session available for schema introspection")
            return ""
        
        try:
            # Get all tables
            tables_result = await self.db.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result.fetchall()]
            
            if not tables:
                logger.warning("No tables found in database")
                return ""
            
            schema_parts = ["Available Tables:"]
            
            # Get columns for each table
            for table in tables:
                columns_result = await self.db.execute(text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                    ORDER BY ordinal_position
                """), {"table_name": table})
                
                columns = [(row[0], row[1]) for row in columns_result.fetchall()]
                column_names = [col[0] for col in columns]
                
                if column_names:
                    schema_parts.append(f"- {table} ({', '.join(column_names)})")
            
            # Get relationships (foreign keys)
            relationships_result = await self.db.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name
            """))
            
            relationships = [
                (row[0], row[1], row[2], row[3])
                for row in relationships_result.fetchall()
            ]
            
            if relationships:
                schema_parts.append("\nRelationships:")
                for rel in relationships:
                    schema_parts.append(
                        f"- {rel[0]}.{rel[1]} -> {rel[2]}.{rel[3]}"
                    )
            
            schema_info = "\n".join(schema_parts)
            logger.debug(f"Retrieved dynamic schema info: {len(tables)} tables, {len(relationships)} relationships")
            return schema_info
            
        except Exception as e:
            logger.warning(f"Error retrieving dynamic schema info: {e}")
            return ""
    
    def _determine_complexity(self, query_understanding: Dict[str, Any]) -> QueryComplexity:
        """
        Determine query complexity for model selection.
        
        Args:
            query_understanding: Query understanding output
        
        Returns:
            QueryComplexity level
        """
        num_tables = len(query_understanding.get("tables", []))
        has_aggregations = len(query_understanding.get("aggregations", [])) > 0
        has_group_by = len(query_understanding.get("group_by", [])) > 0
        
        if num_tables >= 3 or (has_aggregations and has_group_by and num_tables >= 2):
            return QueryComplexity.COMPLEX
        elif num_tables >= 2 or has_aggregations:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean and normalize SQL query.
        
        Args:
            sql: Raw SQL from LLM
        
        Returns:
            Cleaned SQL string
        """
        if not sql:
            return ""
        
        # Remove markdown code blocks (handle various formats)
        sql = sql.strip()
        
        # Remove ```sql or ``` at start
        if sql.startswith("```sql"):
            sql = sql[6:].strip()
        elif sql.startswith("```"):
            sql = sql[3:].strip()
        
        # Remove ``` at end
        if sql.endswith("```"):
            sql = sql[:-3].strip()
        
        # Remove any leading/trailing whitespace
        sql = sql.strip()
        
        # Extract SQL if it's in a code block or has extra text
        # Look for SELECT statement
        import re
        select_match = re.search(r'(SELECT\s+.*?)(?:;|$)', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            sql = select_match.group(1).strip()
        
        # Remove any explanatory text before SELECT
        lines = sql.split('\n')
        sql_lines = []
        found_select = False
        for line in lines:
            line = line.strip()
            if line.upper().startswith('SELECT'):
                found_select = True
            if found_select:
                sql_lines.append(line)
        
        if sql_lines:
            sql = ' '.join(sql_lines)
        
        sql = sql.strip()
        
        # Remove trailing semicolon if present (we'll add it consistently)
        if sql.endswith(";"):
            sql = sql[:-1].strip()
        
        # Ensure SQL ends with semicolon
        if sql and not sql.endswith(";"):
            sql = sql + ";"
        
        return sql
    
    async def _generate_fallback_sql(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str
    ) -> str:
        """
        Generate SQL using a simpler fallback approach.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
        
        Returns:
            Generated SQL query string
        """
        try:
            tables = query_understanding.get("tables", [])
            columns = query_understanding.get("columns", [])
            filters = query_understanding.get("filters", [])
            aggregations = query_understanding.get("aggregations", [])
            group_by = query_understanding.get("group_by", [])
            order_by = query_understanding.get("order_by")
            
            if not tables:
                # Try to infer table from query by searching database schema
                query_lower = natural_language_query.lower()
                inferred_table = await self._infer_table_from_query(query_lower)
                if inferred_table:
                    tables = [inferred_table]
            
            if not tables:
                raise ValueError("Cannot determine table from query")
            
            table = tables[0]
            
            # Build SELECT clause
            if aggregations:
                agg_func = aggregations[0].upper()
                if agg_func == "COUNT":
                    select_clause = "SELECT COUNT(*) as count"
                elif agg_func == "SUM":
                    col = columns[0] if columns else "total_amount"
                    select_clause = f"SELECT SUM({col}) as total"
                elif agg_func == "AVG":
                    col = columns[0] if columns else "total_amount"
                    select_clause = f"SELECT AVG({col}) as average"
                elif agg_func == "MAX":
                    col = columns[0] if columns else "price"
                    select_clause = f"SELECT MAX({col}) as maximum"
                elif agg_func == "MIN":
                    col = columns[0] if columns else "price"
                    select_clause = f"SELECT MIN({col}) as minimum"
                else:
                    select_clause = "SELECT *"
            else:
                if columns:
                    select_clause = f"SELECT {', '.join(columns[:5])}"  # Limit to 5 columns
                else:
                    select_clause = "SELECT *"
            
            # Build FROM clause
            from_clause = f"FROM {table}"
            
            # Build WHERE clause
            where_clause = ""
            if filters:
                conditions = []
                for f in filters[:3]:  # Limit to 3 conditions
                    col = f.get("column", "")
                    op = f.get("operator", "=")
                    val = f.get("value", "")
                    if col and val:
                        if isinstance(val, str) and not val.isdigit():
                            conditions.append(f"{col} {op} '{val}'")
                        else:
                            conditions.append(f"{col} {op} {val}")
                if conditions:
                    where_clause = f"WHERE {' AND '.join(conditions)}"
            
            # Build GROUP BY clause
            group_by_clause = ""
            if group_by:
                group_by_clause = f"GROUP BY {', '.join(group_by)}"
            
            # Build ORDER BY clause
            order_by_clause = ""
            if order_by:
                col = order_by.get("column", "")
                direction = order_by.get("direction", "ASC").upper()
                if col:
                    order_by_clause = f"ORDER BY {col} {direction}"
            
            # Build LIMIT clause
            limit_clause = ""
            if not aggregations or group_by:
                limit_clause = "LIMIT 100"
            
            # Combine all clauses
            sql_parts = [select_clause, from_clause]
            if where_clause:
                sql_parts.append(where_clause)
            if group_by_clause:
                sql_parts.append(group_by_clause)
            if order_by_clause:
                sql_parts.append(order_by_clause)
            if limit_clause:
                sql_parts.append(limit_clause)
            
            sql = " ".join(sql_parts) + ";"
            
            logger.info(f"Generated fallback SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"Error in fallback SQL generation: {e}")
            raise ValueError(f"Failed to generate fallback SQL: {e}")
    
    async def _infer_table_from_query(self, query_lower: str) -> Optional[str]:
        """
        Infer table name from query by searching database schema.
        
        Args:
            query_lower: Lowercase natural language query
        
        Returns:
            Inferred table name or None
        """
        if not self.db:
            return None
        
        try:
            # Get all tables
            result = await self.db.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            all_tables = [row[0].lower() for row in result.fetchall()]
            
            # Try to match query terms with table names
            for table in all_tables:
                # Check if table name (singular or plural) appears in query
                table_singular = table.rstrip('s')  # Remove trailing 's'
                if table in query_lower or table_singular in query_lower:
                    # Get the actual table name (with correct case)
                    actual_table = await self.db.execute(text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND LOWER(table_name) = :table_name
                        LIMIT 1
                    """), {"table_name": table})
                    row = actual_table.fetchone()
                    if row:
                        return row[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error inferring table from query: {e}")
            return None

