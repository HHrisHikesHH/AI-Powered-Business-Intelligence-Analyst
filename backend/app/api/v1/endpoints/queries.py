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
from app.services.token_tracker import token_tracker

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for natural language query."""
    query: str
    user_id: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 100


class QueryResponse(BaseModel):
    """Response model for query execution."""
    query_id: str
    natural_language_query: str
    generated_sql: Optional[str] = None
    results: Optional[list] = None
    analysis: Optional[dict] = None
    visualization: Optional[dict] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    pagination: Optional[dict] = None
    cost_breakdown: Optional[dict] = None


@router.post("/", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept natural language query and return SQL results with analysis and visualization.
    
    Uses specialized multi-agent pipeline with:
    - Query Understanding Agent (intent extraction)
    - SQL Generation Agent (with RAG from pgvector)
    - SQL Validation
    - Query Execution
    - Analysis Agent (insights and recommendations)
    - Visualization Agent (chart configuration)
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
        
        # Track tokens for this query
        token_tracker.query_tokens[query_id] = []
        
        # Process query through pipeline
        result = await orchestrator.process_query(request.query)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Check if validation passed
        if not result.get("validation_passed", False):
            error_msg = result.get("error", "SQL validation failed")
            logger.warning(f"Query validation failed: {error_msg}")
        
        # Apply pagination to results
        results = result.get("results", [])
        total_results = len(results)
        page = max(1, request.page or 1)
        page_size = max(1, min(1000, request.page_size or 100))  # Max 1000 per page
        
        paginated_results = results
        pagination_info = None
        
        if total_results > 0:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_results = results[start_idx:end_idx]
            
            pagination_info = {
                "page": page,
                "page_size": page_size,
                "total_results": total_results,
                "total_pages": (total_results + page_size - 1) // page_size,
                "has_next": end_idx < total_results,
                "has_previous": page > 1
            }
        
        # Get cost breakdown from token tracker
        from app.services.token_tracker import token_tracker
        cost_breakdown = {
            "tokens": token_tracker.get_query_tokens(query_id),
            "cost": token_tracker.get_query_cost(query_id)
        }
        
        response = QueryResponse(
            query_id=query_id,
            natural_language_query=request.query,
            generated_sql=result.get("sql", ""),
            results=paginated_results,
            analysis=result.get("analysis"),
            visualization=result.get("visualization"),
            error=result.get("error") if not result.get("validation_passed", False) else None,
            execution_time_ms=result.get("execution_time_ms") or execution_time,
            pagination=pagination_info,
            cost_breakdown=cost_breakdown
        )
        
        # Cache successful results (only if validation passed and no errors)
        if result.get("validation_passed", False) and not result.get("error"):
            await cache_service.set_with_type(cache_key, response.dict(), "query_result")
        
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

