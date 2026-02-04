"""
Schema Introspection Service.
Introspects database schema and generates embeddings for RAG.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from loguru import logger
from app.core.pgvector_client import vector_store
from typing import Dict, List
import json


class SchemaIntrospector:
    """Service for introspecting database schema and generating embeddings."""
    
    def __init__(self, db: AsyncSession, schema: str = None):
        self.db = db
        self.vector_store = vector_store
        from app.core.config import settings
        self.schema = schema or settings.DATABASE_SCHEMA
    
    async def introspect_and_embed(self) -> Dict[str, int]:
        """
        Introspect database schema and generate embeddings.
        
        Returns:
            Dictionary with counts of embedded elements
        """
        try:
            logger.info("Starting schema introspection and embedding generation...")
            
            counts = {
                "tables": 0,
                "columns": 0,
                "relationships": 0
            }
            
            # Get all tables
            tables = await self._get_tables()
            counts["tables"] = len(tables)
            
            # Embed each table
            for table in tables:
                await self._embed_table(table)
                
                # Get columns for this table
                columns = await self._get_columns(table)
                counts["columns"] += len(columns)
                
                # Embed each column
                for column in columns:
                    await self._embed_column(table, column)
            
            # Embed relationships
            relationships = await self._get_relationships()
            counts["relationships"] = len(relationships)
            
            for rel in relationships:
                await self._embed_relationship(rel)
            
            logger.info(f"Schema introspection complete: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Error during schema introspection: {e}")
            raise
    
    async def _get_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        from app.core.database import get_db_adapter
        adapter = get_db_adapter()
        return await adapter.get_tables(self.db, schema=self.schema)
    
    async def _get_columns(self, table_name: str) -> List[Dict]:
        """Get columns for a table."""
        from app.core.database import get_db_adapter
        adapter = get_db_adapter()
        return await adapter.get_columns(self.db, table_name, schema=self.schema)
    
    async def _get_relationships(self) -> List[Dict]:
        """Get foreign key relationships."""
        from app.core.database import get_db_adapter
        adapter = get_db_adapter()
        return await adapter.get_relationships(self.db, schema=self.schema)
    
    async def _embed_table(self, table_name: str):
        """Generate embedding for a table."""
        columns = await self._get_columns(table_name)
        column_names = [col["name"] for col in columns]
        
        # Create text representation
        text_repr = f"Table: {table_name}\nColumns: {', '.join(column_names)}"
        
        # Create metadata
        metadata = {
            "type": "table",
            "name": table_name,
            "columns": column_names
        }
        
        # Generate embedding
        element_id = f"table:{table_name}"
        await self.vector_store.add_schema_element(
            element_id=element_id,
            text=text_repr,
            metadata=metadata
        )
        
        logger.debug(f"Embedded table: {table_name}")
    
    async def _embed_column(self, table_name: str, column: Dict):
        """Generate embedding for a column."""
        # Create text representation
        text_repr = f"Column: {table_name}.{column['name']} ({column['data_type']})"
        
        # Create metadata
        metadata = {
            "type": "column",
            "table": table_name,
            "name": column["name"],
            "data_type": column["data_type"],
            "is_nullable": column["is_nullable"]
        }
        
        # Generate embedding
        element_id = f"column:{table_name}.{column['name']}"
        await self.vector_store.add_schema_element(
            element_id=element_id,
            text=text_repr,
            metadata=metadata
        )
        
        logger.debug(f"Embedded column: {table_name}.{column['name']}")
    
    async def _embed_relationship(self, relationship: Dict):
        """Generate embedding for a relationship."""
        # Create text representation
        text_repr = (
            f"Relationship: {relationship['table']}.{relationship['column']} "
            f"-> {relationship['foreign_table']}.{relationship['foreign_column']}"
        )
        
        # Create metadata
        metadata = {
            "type": "relationship",
            "table": relationship["table"],
            "column": relationship["column"],
            "foreign_table": relationship["foreign_table"],
            "foreign_column": relationship["foreign_column"]
        }
        
        # Generate embedding
        element_id = f"rel:{relationship['table']}.{relationship['column']}"
        await self.vector_store.add_schema_element(
            element_id=element_id,
            text=text_repr,
            metadata=metadata
        )
        
        logger.debug(f"Embedded relationship: {text_repr}")


async def ensure_schema_embeddings(db: AsyncSession) -> bool:
    """
    Ensure schema embeddings exist. Generate if they don't.
    
    Args:
        db: Database session
    
    Returns:
        True if embeddings were generated or already exist
    """
    try:
        # Check if embeddings exist
        from app.core.pgvector_client import get_pg_pool
        pool = await get_pg_pool()
        
        try:
            async with pool.acquire() as conn:
                # First ensure pgvector extension exists
                ext_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if not ext_exists:
                    logger.info("Creating pgvector extension...")
                    try:
                        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                        logger.info("pgvector extension created successfully")
                    except Exception as ext_error:
                        logger.error(f"Failed to create pgvector extension: {ext_error}")
                        logger.warning("Schema embeddings cannot be created without pgvector extension")
                        return False
                
                # Then ensure the table exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vector_schema_embeddings (
                        id TEXT PRIMARY KEY,
                        embedding vector(384),
                        document TEXT NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Check count
                result = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM vector_schema_embeddings
                """)
                
                if result and result > 0:
                    logger.info(f"Schema embeddings already exist ({result} elements)")
                    return True
        except Exception as table_error:
            logger.warning(f"Error checking embeddings table: {table_error}, will create embeddings")
        
        # Generate embeddings
        logger.info("No schema embeddings found, generating...")
        introspector = SchemaIntrospector(db)
        counts = await introspector.introspect_and_embed()
        
        logger.info(f"Schema embeddings generated: {counts}")
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring schema embeddings: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't fail startup if embeddings can't be generated
        return False

