"""
Redis client for caching and Celery broker.
Provides async Redis operations for caching query results and schema data.
"""
import redis.asyncio as redis
from loguru import logger
from app.core.config import settings
from typing import Optional
import json
from datetime import timedelta

redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def init_redis():
    """Initialize Redis connection."""
    try:
        client = await get_redis()
        await client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


class CacheService:
    """Service for caching operations."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get Redis client."""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        client = await self._get_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set value in cache with TTL (default 1 hour)."""
        client = await self._get_client()
        await client.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    async def delete(self, key: str):
        """Delete key from cache."""
        client = await self._get_client()
        await client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._get_client()
        return await client.exists(key) > 0


cache_service = CacheService()

