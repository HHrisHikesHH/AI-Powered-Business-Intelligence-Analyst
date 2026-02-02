"""
SQL Generation Agent.
Generates SQL queries based on query understanding and schema context.
Uses RAG to retrieve relevant schema information from pgvector.
"""
from loguru import logger
from app.core.llm_client import llm_service, QueryComplexity
from app.core.pgvector_client import vector_store
from app.agents.prompts import format_sql_generation_prompt, SQL_GENERATION_FEW_SHOT_EXAMPLES
from typing import Dict, Any, List, Optional
import json


class SQLGenerationAgent:
    """Agent responsible for generating SQL queries from natural language."""
    
    def __init__(self):
        self.llm = llm_service
        self.vector_store = vector_store
    
    async def generate_sql(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        use_rag: bool = True
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
            
            # Retrieve schema context using RAG
            schema_context = ""
            if use_rag:
                schema_context = await self._retrieve_schema_context(
                    query_understanding,
                    natural_language_query
                )
            
            # If RAG didn't return enough context, add basic schema info
            if not schema_context or len(schema_context) < 50:
                schema_context = self._get_basic_schema_info()
            
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
                        max_tokens=800,  # Increased for complex queries
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
    
    def _get_basic_schema_info(self) -> str:
        """Get basic schema information as fallback."""
        return """Available Tables:
- customers (id, name, email, created_at, city, country, phone)
- products (id, name, category, price, stock_quantity, description, created_at)
- orders (id, customer_id, order_date, total_amount, status, shipping_address)
- order_items (id, order_id, product_id, quantity, line_total)

Relationships:
- orders.customer_id -> customers.id
- order_items.order_id -> orders.id
- order_items.product_id -> products.id"""
    
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
                # Try to infer table from query
                query_lower = natural_language_query.lower()
                if "customer" in query_lower:
                    tables = ["customers"]
                elif "product" in query_lower:
                    tables = ["products"]
                elif "order" in query_lower:
                    tables = ["orders"]
                elif "order item" in query_lower:
                    tables = ["order_items"]
            
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

