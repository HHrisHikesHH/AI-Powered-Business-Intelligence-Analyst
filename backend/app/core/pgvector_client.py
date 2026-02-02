"""
pgvector client for vector storage and retrieval using PostgreSQL.
Used for storing schema embeddings and query history for RAG.
"""
import asyncpg
from loguru import logger
from app.core.config import settings
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
import json

# Initialize sentence transformer model
embedding_model: Optional[SentenceTransformer] = None
_pg_pool: Optional[asyncpg.Pool] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global embedding_model
    if embedding_model is None:
        logger.info("Loading sentence transformer model...")
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
    return embedding_model


async def get_pg_pool() -> asyncpg.Pool:
    """Get or initialize PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool is None:
        try:
            _pg_pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=1,
                max_size=10
            )
            logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    return _pg_pool


async def init_pgvector():
    """Initialize pgvector extension and verify connectivity."""
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            # Check if pgvector extension exists
            ext_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            if not ext_exists:
                logger.info("pgvector extension not found, creating it...")
                try:
                    # Try to create the extension
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    logger.info("pgvector extension created successfully")
                except Exception as ext_error:
                    logger.error(f"Failed to create pgvector extension: {ext_error}")
                    logger.warning("Please ensure pgvector is installed in your PostgreSQL database.")
                    logger.info("For Ubuntu/Debian: sudo apt-get install postgresql-XX-pgvector")
                    logger.info("Or run manually: CREATE EXTENSION IF NOT EXISTS vector;")
                    raise
            else:
                logger.info("pgvector extension verified")
            
            # Verify connection
            await conn.fetchval("SELECT 1")
            logger.info("PostgreSQL connection verified")
    except Exception as e:
        logger.error(f"Failed to initialize pgvector: {e}")
        raise


async def close_pg_pool():
    """Close PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")


class VectorStore:
    """Service for vector storage operations using pgvector."""
    
    def __init__(self, collection_name: str = "schema_embeddings"):
        self.collection_name = collection_name
        self.embedding_model = get_embedding_model()
        self._tables_ensured = False
    
    async def _ensure_tables(self):
        """Ensure vector tables exist for this collection."""
        pool = await get_pg_pool()
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
                    raise RuntimeError(
                        "pgvector extension is required but could not be created. "
                        "Please install it manually: CREATE EXTENSION IF NOT EXISTS vector;"
                    ) from ext_error
            
            # Create table for this collection if it doesn't exist
            table_name = f"vector_{self.collection_name}"
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    embedding vector(384),
                    document TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for similarity search
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
                ON {table_name} 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            logger.info(f"Vector table {table_name} ready")
            self._tables_ensured = True
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def add_schema_element(self, element_id: str, text: str, metadata: Dict):
        """Add schema element (table, column) to vector store."""
        if not self._tables_ensured:
            await self._ensure_tables()
        pool = await get_pg_pool()
        embedding = self.generate_embedding(text)
        table_name = f"vector_{self.collection_name}"
        
        async with pool.acquire() as conn:
            # Convert embedding list to pgvector format: '[1,2,3]'
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            await conn.execute(f"""
                INSERT INTO {table_name} (id, embedding, document, metadata)
                VALUES ($1, $2::vector, $3, $4)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    document = EXCLUDED.document,
                    metadata = EXCLUDED.metadata
            """, element_id, embedding_str, text, json.dumps(metadata))
    
    async def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar schema elements."""
        if not self._tables_ensured:
            await self._ensure_tables()
        pool = await get_pg_pool()
        query_embedding = self.generate_embedding(query)
        table_name = f"vector_{self.collection_name}"
        
        async with pool.acquire() as conn:
            # Convert query embedding to pgvector format
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            # Use cosine distance for similarity search
            results = await conn.fetch(f"""
                SELECT 
                    id,
                    document,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {table_name}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, query_embedding_str, n_results)
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                'id': row['id'],
                'document': row['document'],
                'metadata': json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
                'distance': 1 - row['similarity']  # Convert similarity to distance
            })
        return formatted_results


# Global vector store instance
vector_store = VectorStore()

