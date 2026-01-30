"""
Celery tasks for generating embeddings and updating vector store.
"""
import asyncio
from app.celery_app import celery_app
from app.core.pgvector_client import VectorStore
from loguru import logger


@celery_app.task(name="generate_schema_embeddings")
def generate_schema_embeddings_task(schema_elements: list):
    """
    Generate embeddings for schema elements and store in pgvector.
    
    Args:
        schema_elements: List of dicts with 'id', 'text', and 'metadata' keys
    """
    try:
        async def _generate():
            vector_store = VectorStore()
            for element in schema_elements:
                await vector_store.add_schema_element(
                    element_id=element['id'],
                    text=element['text'],
                    metadata=element['metadata']
                )
            logger.info(f"Generated embeddings for {len(schema_elements)} schema elements")
            return {"status": "success", "count": len(schema_elements)}
        
        return asyncio.run(_generate())
    except Exception as e:
        logger.error(f"Error generating schema embeddings: {e}")
        raise


@celery_app.task(name="update_query_embeddings")
def update_query_embeddings_task(query_id: str, query_text: str, sql: str):
    """
    Store query embedding for RAG retrieval.
    
    Args:
        query_id: Unique identifier for the query
        query_text: Natural language query
        sql: Generated SQL query
    """
    try:
        async def _update():
            # Create a separate collection for query history
            query_store = VectorStore(collection_name="query_history")
            await query_store.add_schema_element(
                element_id=query_id,
                text=f"{query_text}\nSQL: {sql}",
                metadata={"query_text": query_text, "sql": sql}
            )
            logger.info(f"Stored query embedding for query {query_id}")
            return {"status": "success", "query_id": query_id}
        
        return asyncio.run(_update())
    except Exception as e:
        logger.error(f"Error updating query embeddings: {e}")
        raise

