"""
FastAPI main application entry point.
Handles query acceptance and routing to appropriate agents.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import init_db, get_db
from app.core.redis_client import init_redis
from app.core.pgvector_client import init_pgvector, close_pg_pool
from app.services.schema_introspection import ensure_schema_embeddings

app = FastAPI(
    title="AI-Powered Business Intelligence Analyst",
    description="Natural language to SQL query system with multi-agent architecture",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting AI-Powered BI Analyst Backend...")
    try:
        await init_db()
        await init_redis()
        await init_pgvector()
        
        # Initialize schema embeddings for RAG (if not already present)
        async for db in get_db():
            await ensure_schema_embeddings(db)
            break
        
        logger.info("Backend started successfully - all services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down backend...")
    from app.core.redis_client import close_redis
    await close_redis()
    await close_pg_pool()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI-Powered Business Intelligence Analyst",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "pgvector": "connected"
    }

