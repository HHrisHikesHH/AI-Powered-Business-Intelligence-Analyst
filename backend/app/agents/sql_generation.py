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
        previous_sql: Optional[str] = None,
        complexity: Optional[Any] = None
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
            
            # ALWAYS get actual schema from database first (grounding)
            actual_schema = await self._get_dynamic_schema_info()
            
            # Ground query understanding against actual schema (remove non-existent columns)
            grounded_understanding = await self._ground_query_understanding(
                query_understanding,
                actual_schema
            )
            
            # Retrieve additional schema context using hybrid RAG (for relationships, examples)
            schema_context = actual_schema  # Start with actual schema
            if use_rag:
                if self.hybrid_rag:
                    # Use hybrid RAG (vector + keyword + graph-based) for additional context
                    rag_results = await self.hybrid_rag.search(
                        query=natural_language_query,
                        query_understanding=grounded_understanding,
                        n_results=10
                    )
                    rag_context = self.hybrid_rag.format_context(rag_results)
                    if rag_context:
                        schema_context = f"{actual_schema}\n\nAdditional Context:\n{rag_context}"
                else:
                    # Fallback to vector-only RAG
                    rag_context = await self._retrieve_schema_context(
                        grounded_understanding,
                        natural_language_query
                    )
                    if rag_context:
                        schema_context = f"{actual_schema}\n\nAdditional Context:\n{rag_context}"
            
            # Get available tables for context
            schema_dict = await self._parse_schema_info()
            available_tables = list(schema_dict.keys())
            
            # CRITICAL: Validate that we have at least one valid table before proceeding
            original_tables = query_understanding.get("tables", [])
            grounded_tables = grounded_understanding.get("tables", [])
            
            # If no valid tables exist, fail immediately with clear error
            if len(grounded_tables) == 0:
                if len(original_tables) > 0:
                    # User asked about tables that don't exist
                    removed_tables = [t for t in original_tables if t.lower() not in [vt.lower() for vt in available_tables]]
                    raise ValueError(
                        f"The query references table(s) that do NOT exist in the database: {', '.join(removed_tables)}. "
                        f"Available tables in the database: {', '.join(available_tables)}. "
                        f"Please reformulate your query using only the available tables."
                    )
                else:
                    # Query understanding didn't identify any tables
                    raise ValueError(
                        f"Cannot generate SQL: No valid tables identified from the query. "
                        f"The query may reference entities that don't exist in the database. "
                        f"Available tables: {', '.join(available_tables)}"
                    )
            
            # Check if grounding removed important elements
            schema_limitation_note = ""
            original_filters = query_understanding.get("filters", [])
            grounded_filters = grounded_understanding.get("filters", [])
            
            # If critical filters were removed, we should inform the user
            if len(original_filters) > len(grounded_filters):
                removed_filters = [f.get("column", "unknown") for f in original_filters 
                                 if f not in grounded_filters]
                
                schema_limitation_note = f"""
⚠️ SCHEMA LIMITATION DETECTED:
The user's query referenced columns that do not exist in the database: {', '.join(removed_filters)}
These columns have been removed from the query understanding.

IMPORTANT: You MUST NOT use these non-existent columns in your SQL. 
Generate SQL using ONLY the columns that exist in the schema provided above.
If the query cannot be answered without these columns, you may need to return a simpler query or omit that filter.
"""
            # If critical filters were removed, we should inform the user
            elif len(original_filters) > len(grounded_filters):
                removed_filters = [f.get("column", "unknown") for f in original_filters 
                                 if f not in grounded_filters]
                
                schema_limitation_note = f"""
⚠️ SCHEMA LIMITATION DETECTED:
The user's query referenced columns that do not exist in the database: {', '.join(removed_filters)}
These columns have been removed from the query understanding.

IMPORTANT: You MUST NOT use these non-existent columns in your SQL. 
Generate SQL using ONLY the columns that exist in the schema provided above.
If the query cannot be answered without these columns, you may need to return a simpler query or omit that filter.
"""
            
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
            
            # Format prompt with context (use grounded understanding)
            prompt = format_sql_generation_prompt(
                query_understanding=grounded_understanding,
                schema_context=schema_context,
                few_shot_examples=SQL_GENERATION_FEW_SHOT_EXAMPLES
            )
            
            # Add grounded query understanding as context
            understanding_str = json.dumps(grounded_understanding, indent=2)
            
            # Add explicit validation reminder
            validation_reminder = f"""
✅ VALIDATION CHECK:
- Query Understanding Tables: {grounded_tables}
- Available Tables in Schema: {available_tables}
- All required tables exist: {'YES' if all(t.lower() in [at.lower() for at in available_tables] for t in grounded_tables) else 'NO - DO NOT GENERATE SQL'}

⚠️ REMINDER: If any table in the query understanding does not exist in the schema above, DO NOT generate SQL.
"""
            
            full_prompt = f"""Query Understanding:
{understanding_str}

Original Query: {natural_language_query}

{validation_reminder}

{schema_limitation_note}

{error_context}

{prompt}"""
            
            # Use provided complexity or determine from query understanding
            if complexity is None:
                complexity = self._determine_complexity(query_understanding)
            
            # Generate SQL with retry logic
            sql = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    response = await self.llm.generate_completion(
                        prompt=full_prompt,
                        system_prompt="""You are a SQL Generation Agent. Your ONLY job is to generate a valid PostgreSQL SELECT query.

🚨 CRITICAL ANTI-HALLUCINATION RULES:
1. BEFORE generating SQL, verify ALL tables in query_understanding.tables exist in the schema
2. If ANY table does not exist, return an ERROR message starting with "ERROR:" instead of SQL
3. DO NOT default to "customers" or any other table if the requested table doesn't exist
4. DO NOT generate SQL if query_understanding.tables is empty
5. ONLY generate SQL if ALL required tables are present in the schema

CRITICAL RULES:
1. Return ONLY the SQL query - no explanations, no markdown, no code blocks
2. OR return an error message starting with "ERROR:" if tables don't exist
3. Start directly with SELECT (or ERROR:)
4. Use proper PostgreSQL syntax
5. Include all necessary clauses (FROM, WHERE, GROUP BY, ORDER BY, LIMIT)
6. End with semicolon

Example format:
SELECT * FROM customers LIMIT 100;

OR if table doesn't exist:
ERROR: The table 'cars' does not exist in the database. Available tables: customers, products, orders, order_items

Do NOT include:
- Explanations
- Markdown code blocks (```sql)
- Comments
- Any text before or after the SQL (except ERROR: prefix)

Just the SQL query or ERROR message, nothing else.""",
                        temperature=0.1,  # Very low temperature for deterministic SQL
                        max_tokens=800,
                        complexity=complexity,
                        auto_select_model=True
                    )
                    
                    # Check if response is valid
                    if response and response.strip():
                        # Check if LLM returned an error message
                        response_upper = response.strip().upper()
                        if response_upper.startswith("ERROR:"):
                            error_msg = response.strip()
                            logger.warning(f"LLM detected schema issue: {error_msg}")
                            raise ValueError(error_msg.replace("ERROR:", "").strip())
                        
                        sql = self._clean_sql(response)
                        
                        # Validate SQL is not empty and starts with SELECT
                        if sql and sql.strip().upper().startswith("SELECT"):
                            # Additional validation: Check that SQL uses only valid tables
                            sql_tables = self._extract_tables_from_sql(sql)
                            schema_tables_lower = [t.lower() for t in available_tables]
                            invalid_tables = [t for t in sql_tables if t.lower() not in schema_tables_lower]
                            
                            if invalid_tables:
                                logger.warning(f"SQL contains invalid tables: {invalid_tables}")
                                raise ValueError(
                                    f"Generated SQL references non-existent tables: {', '.join(invalid_tables)}. "
                                    f"Available tables: {', '.join(available_tables)}"
                                )
                            
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
            
        except ValueError as e:
            # Re-raise ValueError (these are schema limitation errors we want to propagate)
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "available tables" in error_msg.lower():
                logger.warning(f"Schema limitation detected: {error_msg}")
                raise ValueError(error_msg)
            else:
                raise ValueError(f"Failed to generate SQL: {error_msg}")
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
    
    async def _ground_query_understanding(
        self,
        query_understanding: Dict[str, Any],
        schema_info: str
    ) -> Dict[str, Any]:
        """
        Ground query understanding against actual schema.
        Removes non-existent columns and tables from query understanding.
        
        Args:
            query_understanding: Original query understanding
            schema_info: Schema information string
        
        Returns:
            Grounded query understanding with only valid columns/tables
        """
        if not self.db:
            logger.warning("No database session for schema grounding")
            return query_understanding
        
        try:
            # Parse schema info to get actual columns per table
            schema_dict = await self._parse_schema_info()
            
            grounded = query_understanding.copy()
            
            # Validate and filter tables
            tables = grounded.get("tables", [])
            valid_tables = []
            for table in tables:
                if table.lower() in [t.lower() for t in schema_dict.keys()]:
                    # Find actual table name (case-sensitive)
                    actual_table = next(
                        (t for t in schema_dict.keys() if t.lower() == table.lower()),
                        table
                    )
                    valid_tables.append(actual_table)
                else:
                    logger.warning(f"Table '{table}' not found in schema, removing from query understanding")
            
            grounded["tables"] = valid_tables
            
            # Validate and filter columns
            columns = grounded.get("columns", [])
            valid_columns = []
            for col in columns:
                # Check if column exists in any of the valid tables
                found = False
                for table in valid_tables:
                    if col.lower() in [c.lower() for c in schema_dict.get(table, [])]:
                        found = True
                        break
                
                if found:
                    valid_columns.append(col)
                else:
                    logger.warning(f"Column '{col}' not found in schema, removing from query understanding")
            
            grounded["columns"] = valid_columns
            
            # Validate and filter filters
            filters = grounded.get("filters", [])
            valid_filters = []
            for f in filters:
                col = f.get("column", "")
                # Check if filter column exists
                found = False
                for table in valid_tables:
                    if col.lower() in [c.lower() for c in schema_dict.get(table, [])]:
                        found = True
                        break
                
                if found:
                    valid_filters.append(f)
                else:
                    logger.warning(f"Filter column '{col}' not found in schema, removing filter")
            
            grounded["filters"] = valid_filters
            
            # Validate group_by columns
            group_by = grounded.get("group_by", [])
            valid_group_by = []
            for col in group_by:
                found = False
                for table in valid_tables:
                    if col.lower() in [c.lower() for c in schema_dict.get(table, [])]:
                        found = True
                        break
                
                if found:
                    valid_group_by.append(col)
                else:
                    logger.warning(f"GROUP BY column '{col}' not found in schema, removing")
            
            grounded["group_by"] = valid_group_by
            
            # Validate order_by column
            order_by = grounded.get("order_by")
            if order_by and isinstance(order_by, dict):
                col = order_by.get("column", "")
                if col:
                    found = False
                    for table in valid_tables:
                        if col.lower() in [c.lower() for c in schema_dict.get(table, [])]:
                            found = True
                            break
                    
                    if not found:
                        logger.warning(f"ORDER BY column '{col}' not found in schema, removing")
                        grounded["order_by"] = None
            
            # If query understanding was modified, log it
            if (len(valid_tables) < len(tables) or 
                len(valid_columns) < len(columns) or 
                len(valid_filters) < len(filters)):
                logger.warning(
                    f"Query understanding grounded: removed {len(tables) - len(valid_tables)} invalid tables, "
                    f"{len(columns) - len(valid_columns)} invalid columns, "
                    f"{len(filters) - len(valid_filters)} invalid filters"
                )
            
            # If all tables were removed, this is a critical error - user asked about non-existent entity
            if len(tables) > 0 and len(valid_tables) == 0:
                removed_tables = [t for t in tables if t.lower() not in [vt.lower() for vt in schema_dict.keys()]]
                available_tables = list(schema_dict.keys())
                raise ValueError(
                    f"The query references table(s) that do not exist in the database: {', '.join(removed_tables)}. "
                    f"Available tables: {', '.join(available_tables)}. "
                    f"Please reformulate your query using only the available tables."
                )
            
            return grounded
            
        except Exception as e:
            logger.error(f"Error grounding query understanding: {e}")
            return query_understanding
    
    async def _parse_schema_info(self) -> Dict[str, List[str]]:
        """
        Parse schema information into a dictionary of table -> columns.
        
        Returns:
            Dictionary mapping table names to lists of column names
        """
        if not self.db:
            return {}
        
        try:
            result = await self.db.execute(text("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """))
            
            schema_dict = {}
            for row in result.fetchall():
                table_name = row[0]
                column_name = row[1]
                
                if table_name not in schema_dict:
                    schema_dict[table_name] = []
                schema_dict[table_name].append(column_name)
            
            return schema_dict
            
        except Exception as e:
            logger.error(f"Error parsing schema info: {e}")
            return {}
    
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
            
            schema_parts = ["=" * 60]
            schema_parts.append("ACTUAL DATABASE SCHEMA - USE ONLY THESE COLUMNS")
            schema_parts.append("=" * 60)
            schema_parts.append("")
            
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
                    schema_parts.append(f"Table: {table}")
                    schema_parts.append(f"  Columns: {', '.join(column_names)}")
                    schema_parts.append("")
            
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
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """
        Extract table names from SQL query for validation.
        
        Args:
            sql: SQL query string
        
        Returns:
            List of table names found in SQL
        """
        import re
        tables = []
        sql_upper = sql.upper()
        
        # Extract FROM clause
        from_matches = re.findall(r'\bFROM\s+(\w+)', sql_upper)
        tables.extend(from_matches)
        
        # Extract JOIN clauses
        join_matches = re.findall(r'\bJOIN\s+(\w+)', sql_upper)
        tables.extend(join_matches)
        
        # Remove duplicates and normalize
        return list(set([t.lower() for t in tables]))
    
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

