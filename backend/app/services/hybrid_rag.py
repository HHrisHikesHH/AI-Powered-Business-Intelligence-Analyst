"""
Hybrid RAG implementation combining vector search, keyword search, and graph-based retrieval.
"""
from typing import List, Dict, Any, Optional, Set
from loguru import logger
from app.core.pgvector_client import vector_store, get_pg_pool
from app.core.redis_client import cache_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import re
import json
import asyncio
from collections import defaultdict


class HybridRAG:
    """
    Hybrid RAG service combining:
    1. Vector search (semantic similarity via pgvector)
    2. Keyword search (BM25-like exact matching)
    3. Graph-based retrieval (schema relationships via foreign keys)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = vector_store
        self._schema_graph: Optional[Dict[str, Set[str]]] = None
        self._keyword_index: Optional[Dict[str, Dict[str, Any]]] = None
    
    async def search(
        self,
        query: str,
        query_understanding: Dict[str, Any],
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector, keyword, and graph-based retrieval.
        Runs searches in parallel for better performance.
        
        Args:
            query: Natural language query
            query_understanding: Query understanding output
            n_results: Number of results to return
        
        Returns:
            List of relevant schema elements and query examples
        """
        try:
            # Get tables and columns from query understanding
            tables = query_understanding.get("tables", [])
            columns = query_understanding.get("columns", [])
            
            # Run all searches in parallel for better performance
            vector_task = self._vector_search(query, n_results)
            keyword_task = self._keyword_search(tables, columns, n_results)
            graph_task = self._graph_based_retrieval(tables, n_results)
            
            # Execute in parallel
            vector_results, keyword_results, graph_results = await asyncio.gather(
                vector_task,
                keyword_task,
                graph_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            vector_results = vector_results if not isinstance(vector_results, Exception) else []
            keyword_results = keyword_results if not isinstance(keyword_results, Exception) else []
            graph_results = graph_results if not isinstance(graph_results, Exception) else []
            
            # Combine and deduplicate results
            combined_results = self._combine_results(
                vector_results,
                keyword_results,
                graph_results,
                n_results
            )
            
            logger.info(
                f"Hybrid RAG: {len(vector_results)} vector, "
                f"{len(keyword_results)} keyword, "
                f"{len(graph_results)} graph results → {len(combined_results)} combined"
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid RAG search: {e}")
            # Fallback to vector search only
            return await self._vector_search(query, n_results)
    
    async def _vector_search(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        """Vector search using pgvector."""
        try:
            results = await self.vector_store.search_similar(query, n_results=n_results)
            return results or []
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    async def _keyword_search(
        self,
        tables: List[str],
        columns: List[str],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """
        Keyword search using exact matching (BM25-like).
        Searches for exact table and column names.
        """
        try:
            if not tables and not columns:
                return []
            
            # Build keyword index if not exists
            if self._keyword_index is None:
                await self._build_keyword_index()
            
            results = []
            seen = set()
            
            # Search for tables
            for table in tables:
                table_lower = table.lower()
                if table_lower in self._keyword_index:
                    entry = self._keyword_index[table_lower]
                    key = f"{entry['type']}:{entry['name']}"
                    if key not in seen:
                        results.append(entry)
                        seen.add(key)
            
            # Search for columns
            for column in columns:
                column_lower = column.lower()
                # Try to find column in any table
                for table_name, table_data in self._keyword_index.items():
                    if table_data.get("type") == "table":
                        # Check if column exists in this table's metadata
                        table_columns = table_data.get("metadata", {}).get("columns", [])
                        if column_lower in [c.lower() for c in table_columns]:
                            # Create column entry
                            column_entry = {
                                "document": f"Column {column} in table {table_name}",
                                "metadata": {
                                    "type": "column",
                                    "table": table_name,
                                    "name": column,
                                    "columns": table_columns
                                }
                            }
                            key = f"column:{table_name}:{column}"
                            if key not in seen:
                                results.append(column_entry)
                                seen.add(key)
                                break
            
            return results[:n_results]
            
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            return []
    
    async def _graph_based_retrieval(
        self,
        tables: List[str],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """
        Graph-based retrieval using schema relationships.
        When a table is identified, retrieve related tables (1-2 hops via foreign keys).
        """
        try:
            if not tables:
                return []
            
            # Build schema graph if not exists
            if self._schema_graph is None:
                await self._build_schema_graph()
            
            results = []
            seen = set()
            
            # For each table, get related tables (1-2 hops)
            for table in tables:
                table_lower = table.lower()
                
                # Direct relationships (1 hop)
                if table_lower in self._schema_graph:
                    related = self._schema_graph[table_lower]
                    for related_table in related:
                        if related_table not in seen:
                            # Retrieve schema for related table
                            schema_entry = await self._get_table_schema(related_table)
                            if schema_entry:
                                results.append(schema_entry)
                                seen.add(related_table)
                    
                    # 2-hop relationships
                    for related_table in related:
                        if related_table in self._schema_graph:
                            second_hop = self._schema_graph[related_table]
                            for second_table in second_hop:
                                if second_table not in seen and second_table != table_lower:
                                    schema_entry = await self._get_table_schema(second_table)
                                    if schema_entry:
                                        results.append(schema_entry)
                                        seen.add(second_table)
            
            return results[:n_results]
            
        except Exception as e:
            logger.warning(f"Graph-based retrieval failed: {e}")
            return []
    
    async def _build_keyword_index(self):
        """Build in-memory keyword index for fast exact matching with caching."""
        try:
            # Check cache first
            cached = await cache_service.get("rag:keyword_index")
            if cached:
                logger.info("Using cached keyword index")
                self._keyword_index = cached
                return
            
            pool = await get_pg_pool()
            async with pool.acquire() as conn:
                # Get all schema embeddings
                rows = await conn.fetch("""
                    SELECT id, document, metadata
                    FROM vector_schema_embeddings
                """)
                
                self._keyword_index = {}
                
                for row in rows:
                    metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
                    entry_type = metadata.get("type", "unknown")
                    name = metadata.get("name", "")
                    
                    if name:
                        name_lower = name.lower()
                        self._keyword_index[name_lower] = {
                            "document": row['document'],
                            "metadata": metadata,
                            "type": entry_type,
                            "name": name
                        }
                
                logger.info(f"Built keyword index with {len(self._keyword_index)} entries")
                
                # Cache for 24 hours
                await cache_service.set("rag:keyword_index", self._keyword_index, ttl=86400)
                
        except Exception as e:
            logger.error(f"Failed to build keyword index: {e}")
            self._keyword_index = {}
    
    async def _build_schema_graph(self):
        """
        Build schema graph from foreign key relationships with caching.
        Graph structure: {table_name: {related_table1, related_table2, ...}}
        """
        try:
            # Check cache first
            cached = await cache_service.get("rag:schema_graph")
            if cached:
                logger.info("Using cached schema graph")
                # Convert list back to set
                self._schema_graph = {
                    k: set(v) for k, v in cached.items()
                }
                return
            
            pool = await get_pg_pool()
            async with pool.acquire() as conn:
                # Query foreign key relationships
                query = """
                    SELECT
                        tc.table_name AS source_table,
                        ccu.table_name AS target_table
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                """
                
                rows = await conn.fetch(query)
                
                self._schema_graph = defaultdict(set)
                
                for row in rows:
                    source = row['source_table'].lower()
                    target = row['target_table'].lower()
                    self._schema_graph[source].add(target)
                    # Also add reverse relationship for bidirectional traversal
                    self._schema_graph[target].add(source)
                
                logger.info(f"Built schema graph with {len(self._schema_graph)} nodes")
                
                # Cache for 24 hours (convert sets to lists for JSON)
                graph_for_cache = {
                    k: list(v) for k, v in self._schema_graph.items()
                }
                await cache_service.set("rag:schema_graph", graph_for_cache, ttl=86400)
                
        except Exception as e:
            logger.error(f"Failed to build schema graph: {e}")
            self._schema_graph = {}
    
    async def _get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve schema information for a table."""
        try:
            pool = await get_pg_pool()
            async with pool.acquire() as conn:
                # Search in vector store for this table
                results = await self.vector_store.search_similar(
                    f"table {table_name}",
                    n_results=1
                )
                
                if results:
                    return results[0]
                
                # Fallback: query database directly
                columns_query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                
                columns = await conn.fetch(columns_query, table_name)
                
                if columns:
                    column_names = [col['column_name'] for col in columns]
                    return {
                        "document": f"Table: {table_name}\nColumns: {', '.join(column_names)}",
                        "metadata": {
                            "type": "table",
                            "name": table_name,
                            "columns": column_names
                        }
                    }
                
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get table schema for {table_name}: {e}")
            return None
    
    def _combine_results(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        graph_results: List[Dict],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """
        Combine results from different retrieval methods with deduplication.
        Prioritizes: keyword > graph > vector
        """
        combined = []
        seen = set()
        
        # Priority 1: Keyword results (exact matches)
        for result in keyword_results:
            key = self._get_result_key(result)
            if key not in seen:
                combined.append({**result, "source": "keyword"})
                seen.add(key)
        
        # Priority 2: Graph results (related tables)
        for result in graph_results:
            key = self._get_result_key(result)
            if key not in seen:
                combined.append({**result, "source": "graph"})
                seen.add(key)
        
        # Priority 3: Vector results (semantic similarity)
        for result in vector_results:
            key = self._get_result_key(result)
            if key not in seen:
                combined.append({**result, "source": "vector"})
                seen.add(key)
        
        return combined[:n_results]
    
    def _get_result_key(self, result: Dict) -> str:
        """Generate a unique key for a result to detect duplicates."""
        metadata = result.get("metadata", {})
        entry_type = metadata.get("type", "unknown")
        name = metadata.get("name", "")
        table = metadata.get("table", "")
        
        if entry_type == "column" and table:
            return f"{entry_type}:{table}:{name}"
        elif name:
            return f"{entry_type}:{name}"
        else:
            return f"{entry_type}:{hash(str(result))}"
    
    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a context string for SQL generation.
        
        Args:
            results: List of search results
        
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        
        # Group by type
        tables = []
        columns = []
        other = []
        
        for result in results:
            metadata = result.get("metadata", {})
            entry_type = metadata.get("type", "unknown")
            
            if entry_type == "table":
                tables.append(result)
            elif entry_type == "column":
                columns.append(result)
            else:
                other.append(result)
        
        # Format tables
        if tables:
            context_parts.append("Tables:")
            for result in tables:
                metadata = result.get("metadata", {})
                table_name = metadata.get("name", "unknown")
                table_columns = metadata.get("columns", [])
                if table_columns:
                    context_parts.append(f"  - {table_name} ({', '.join(table_columns)})")
                else:
                    context_parts.append(f"  - {table_name}")
        
        # Format columns
        if columns:
            context_parts.append("\nColumns:")
            for result in columns:
                metadata = result.get("metadata", {})
                table = metadata.get("table", "unknown")
                column = metadata.get("name", "unknown")
                data_type = metadata.get("data_type", "")
                context_parts.append(f"  - {table}.{column}" + (f" ({data_type})" if data_type else ""))
        
        # Format other results
        if other:
            context_parts.append("\nAdditional Context:")
            for result in other:
                doc = result.get("document", "")
                if doc:
                    context_parts.append(f"  - {doc}")
        
        return "\n".join(context_parts)

