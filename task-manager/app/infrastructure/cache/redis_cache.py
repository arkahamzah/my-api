"""
Redis implementation of CacheService.
"""
import json
import logging
from typing import Any

from redis.asyncio import Redis

from app.application.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RedisCacheService(CacheService):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning("Cache GET failed for key=%s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning("Cache SET failed for key=%s: %s", key, e)

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning("Cache DELETE failed for key=%s: %s", key, e)

    async def delete_pattern(self, pattern: str) -> None:
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.warning("Cache DELETE_PATTERN failed for pattern=%s: %s", pattern, e)


class NullCacheService(CacheService):
    """No-op cache untuk testing - tidak perlu Redis."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass

    async def delete_pattern(self, pattern: str) -> None:
        pass
