"""
Redis client for caching and Celery broker.
Provides async Redis operations for caching query results and schema data.
"""
import redis.asyncio as redis
from loguru import logger
from app.core.config import settings
from typing import Optional, List, Dict, Any
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
    """
    Enhanced caching service with TTL management and LRU support.
    Supports different cache types with appropriate TTLs.
    """
    
    # Cache TTLs (in seconds)
    TTL_QUERY_RESULT = 3600  # 1 hour for query results
    TTL_QUERY_UNDERSTANDING = 86400  # 24 hours for query understanding
    TTL_SCHEMA = 86400  # 24 hours for schema data
    TTL_EMBEDDING = 86400  # 24 hours for embeddings
    TTL_RAG_INDEX = 86400  # 24 hours for RAG indexes
    
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
    
    async def set_with_type(self, key: str, value: dict, cache_type: str = "query_result"):
        """
        Set value with appropriate TTL based on cache type.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache (query_result, query_understanding, schema, embedding, rag_index)
        """
        ttl_map = {
            "query_result": self.TTL_QUERY_RESULT,
            "query_understanding": self.TTL_QUERY_UNDERSTANDING,
            "schema": self.TTL_SCHEMA,
            "embedding": self.TTL_EMBEDDING,
            "rag_index": self.TTL_RAG_INDEX,
        }
        ttl = ttl_map.get(cache_type, self.TTL_QUERY_RESULT)
        await self.set(key, value, ttl)
    
    async def delete(self, key: str):
        """Delete key from cache."""
        client = await self._get_client()
        await client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._get_client()
        return await client.exists(key) > 0
    
    async def get_many(self, keys: List[str]) -> Dict[str, Optional[dict]]:
        """Get multiple values from cache."""
        client = await self._get_client()
        values = await client.mget(keys)
        result = {}
        for key, value in zip(keys, values):
            if value:
                result[key] = json.loads(value)
            else:
                result[key] = None
        return result
    
    async def set_many(self, items: Dict[str, dict], ttl: int = 3600):
        """Set multiple values in cache."""
        client = await self._get_client()
        pipe = client.pipeline()
        for key, value in items.items():
            pipe.setex(key, ttl, json.dumps(value))
        await pipe.execute()
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching a pattern."""
        client = await self._get_client()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await client.delete(*keys)
        logger.info(f"Cleared {len(keys)} keys matching pattern: {pattern}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        client = await self._get_client()
        info = await client.info("stats")
        return {
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_keys": await client.dbsize(),
        }


cache_service = CacheService()

