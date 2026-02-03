"""
Celery tasks for generating embeddings and updating vector store.
"""
import asyncio
from app.celery_app import celery_app
from app.core.pgvector_client import VectorStore
from loguru import logger


@celery_app.task(name="generate_schema_embeddings", bind=True)
def generate_schema_embeddings_task(self, schema_elements: list, batch_size: int = 50):
    """
    Generate embeddings for schema elements in batches and store in pgvector.
    Optimized for batch processing to improve performance.
    
    Args:
        schema_elements: List of dicts with 'id', 'text', and 'metadata' keys
        batch_size: Number of elements to process in each batch
    """
    try:
        async def _generate():
            vector_store = VectorStore()
            total = len(schema_elements)
            processed = 0
            
            # Process in batches
            for i in range(0, total, batch_size):
                batch = schema_elements[i:i + batch_size]
                
                # Generate embeddings for batch
                for element in batch:
                    await vector_store.add_schema_element(
                        element_id=element['id'],
                        text=element['text'],
                        metadata=element['metadata']
                    )
                
                processed += len(batch)
                
                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'processed': processed,
                        'total': total,
                        'percentage': int((processed / total) * 100)
                    }
                )
                
                logger.info(f"Processed batch: {processed}/{total} schema elements")
            
            logger.info(f"Generated embeddings for {total} schema elements in batches")
            return {
                "status": "success",
                "count": total,
                "batches": (total + batch_size - 1) // batch_size
            }
        
        return asyncio.run(_generate())
    except Exception as e:
        logger.error(f"Error generating schema embeddings: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
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

