"""
Query endpoints for accepting natural language queries.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from app.core.database import get_db
from app.core.redis_client import cache_service
from app.agents.orchestrator import Orchestrator

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query execution."""
    query_id: str
    natural_language_query: str
    generated_sql: Optional[str] = None
    results: Optional[list] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


@router.post("/", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept natural language query and return SQL results.
    
    Phase 1, Week 2: Uses multi-agent pipeline with:
    - Query Understanding Agent
    - SQL Generation Agent (with RAG)
    - SQL Validation
    - Query Execution
    """
    import time
    import uuid
    
    query_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Received query: {request.query}")
        
        # Check cache first
        cache_key = f"query:{hash(request.query)}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return QueryResponse(**cached_result)
        
        # Initialize orchestrator (multi-agent pipeline)
        orchestrator = Orchestrator(db)
        
        # Process query through pipeline
        result = await orchestrator.process_query(request.query)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Check if validation passed
        if not result.get("validation_passed", False):
            error_msg = result.get("error", "SQL validation failed")
            logger.warning(f"Query validation failed: {error_msg}")
        
        response = QueryResponse(
            query_id=query_id,
            natural_language_query=request.query,
            generated_sql=result.get("sql", ""),
            results=result.get("results", []),
            error=result.get("error") if not result.get("validation_passed", False) else None,
            execution_time_ms=execution_time
        )
        
        # Cache successful results (only if validation passed and no errors)
        if result.get("validation_passed", False) and not result.get("error"):
            await cache_service.set(cache_key, response.dict(), ttl=3600)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        execution_time = (time.time() - start_time) * 1000
        return QueryResponse(
            query_id=query_id,
            natural_language_query=request.query,
            error=str(e),
            execution_time_ms=execution_time
        )


@router.get("/{query_id}")
async def get_query_result(query_id: str):
    """Get query result by ID (placeholder for future implementation)."""
    return {"message": "Query result retrieval not yet implemented", "query_id": query_id}

