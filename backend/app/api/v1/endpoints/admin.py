"""
Admin and metrics endpoints for monitoring and observability.
Provides real-time metrics, error statistics, and cost insights.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.metrics import metrics_service


router = APIRouter()


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get real-time admin metrics including:
    - Query success rate and latency
    - Active users
    - Token and cost statistics
    - Error breakdown
    - Cache statistics
    - Simple monthly cost forecast
    """
    # Currently metrics are primarily in-memory; DB is injected for future use if needed
    _ = db  # placeholder to avoid unused warning
    summary = await metrics_service.get_admin_summary()
    return summary


