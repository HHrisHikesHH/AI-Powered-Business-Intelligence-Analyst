"""
Main API router for v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import queries

try:
    from app.api.v1.endpoints import admin  # type: ignore
except ImportError:  # admin module may not exist yet
    admin = None


api_router = APIRouter()

# Include endpoint routers
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])

if admin is not None:
    api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

