"""
Celery application configuration for async task processing.
Used for background tasks like embedding generation and query processing.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_bi_analyst",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

