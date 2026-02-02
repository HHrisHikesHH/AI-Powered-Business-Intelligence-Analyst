"""
Standalone script to generate schema embeddings.
Can be run manually if embeddings weren't created on startup.

Usage:
    cd backend
    python scripts/generate_embeddings.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.pgvector_client import init_pgvector
from app.services.schema_introspection import SchemaIntrospector
from loguru import logger


async def main():
    """Generate schema embeddings."""
    logger.info("Starting schema embedding generation...")
    
    # Initialize pgvector
    await init_pgvector()
    
    # Create database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            introspector = SchemaIntrospector(db)
            counts = await introspector.introspect_and_embed()
            
            logger.info(f"Schema embeddings generated successfully!")
            logger.info(f"  Tables: {counts['tables']}")
            logger.info(f"  Columns: {counts['columns']}")
            logger.info(f"  Relationships: {counts['relationships']}")
            
            print("\n✅ Schema embeddings generated successfully!")
            print(f"   - {counts['tables']} tables")
            print(f"   - {counts['columns']} columns")
            print(f"   - {counts['relationships']} relationships")
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

