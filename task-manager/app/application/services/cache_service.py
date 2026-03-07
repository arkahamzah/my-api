"""
Cache Service - abstraksi cache di application layer.
Infrastructure tidak bocor ke domain/application.
"""
from abc import ABC, abstractmethod
from typing import Any


class CacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None: ...


class CacheKeys:
    """Centralized cache key builder - hindari typo dan inkonsistensi."""

    @staticmethod
    def tenant(tenant_id: str) -> str:
        return f"tenant:{tenant_id}"

    @staticmethod
    def tenant_slug(slug: str) -> str:
        return f"tenant:slug:{slug}"

    @staticmethod
    def tenant_list(skip: int, limit: int) -> str:
        return f"tenant:list:{skip}:{limit}"

    @staticmethod
    def task(task_id: str) -> str:
        return f"task:{task_id}"

    @staticmethod
    def task_list(tenant_id: str, status: str | None, skip: int, limit: int) -> str:
        return f"task:list:{tenant_id}:{status}:{skip}:{limit}"

    @staticmethod
    def tenant_tasks_pattern(tenant_id: str) -> str:
        return f"task:*:{tenant_id}:*"


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
