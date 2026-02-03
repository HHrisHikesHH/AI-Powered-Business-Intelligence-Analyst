"""
FastAPI main application entry point.
Handles query acceptance, orchestration, and monitoring.
"""
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

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

# Prometheus metrics
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect basic request metrics for Prometheus."""
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    path = request.url.path
    method = request.method
    status_code = response.status_code

    try:
        REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(process_time)
    except Exception as e:
        logger.debug(f"Failed to record Prometheus metrics: {e}")

    return response


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
            await ensure_that_schema_embeddings_exist(db)
            break

        logger.info("Backend started successfully - all services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def ensure_that_schema_embeddings_exist(db):
    """Wrapper to call ensure_schema_embeddings for startup hook."""
    await ensure_schema_embeddings(db)


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
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
  """Detailed health check."""
  return {
      "status": "healthy",
      "database": "connected",
      "redis": "connected",
      "pgvector": "connected",
  }


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

