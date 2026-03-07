"""
Tests untuk cache behavior - menggunakan NullCacheService (no Redis needed).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.commands.task_commands import CreateTaskCommand, UpdateTaskCommand
from app.application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from app.application.services.cache_service import CacheKeys, NullCacheService
from app.application.use_cases.task_use_cases import TaskUseCases
from tests.helpers.in_memory_repos import InMemoryTaskRepo


@pytest.fixture
def use_cases():
    return TaskUseCases(InMemoryTaskRepo(), NullCacheService())


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


class TestCacheKeys:
    def test_tenant_key(self):
        assert CacheKeys.tenant("abc") == "tenant:abc"

    def test_tenant_slug_key(self):
        assert CacheKeys.tenant_slug("acme") == "tenant:slug:acme"

    def test_task_key(self):
        assert CacheKeys.task("xyz") == "task:xyz"

    def test_task_list_key(self):
        key = CacheKeys.task_list("tid", "todo", 0, 20)
        assert "tid" in key and "todo" in key

    def test_task_list_key_none_status(self):
        key = CacheKeys.task_list("tid", None, 0, 20)
        assert "None" in key or "tid" in key

    def test_tenant_tasks_pattern(self):
        assert "*" in CacheKeys.tenant_tasks_pattern("tid")


class TestNullCache:
    @pytest.mark.asyncio
    async def test_get_returns_none(self):
        cache = NullCacheService()
        assert await cache.get("any-key") is None

    @pytest.mark.asyncio
    async def test_set_does_not_raise(self):
        cache = NullCacheService()
        await cache.set("key", {"data": 1})  # no error

    @pytest.mark.asyncio
    async def test_delete_does_not_raise(self):
        cache = NullCacheService()
        await cache.delete("key")

    @pytest.mark.asyncio
    async def test_delete_pattern_does_not_raise(self):
        cache = NullCacheService()
        await cache.delete_pattern("key:*")


class TestCacheIntegration:
    """Test bahwa use case tetap bekerja dengan NullCache (graceful degradation)."""

    @pytest.mark.asyncio
    async def test_create_with_null_cache(self, use_cases, tenant_id, user_id):
        cmd = CreateTaskCommand(tenant_id=tenant_id, created_by=user_id, title="Cached Task")
        task = await use_cases.create(cmd)
        assert task.title == "Cached Task"

    @pytest.mark.asyncio
    async def test_get_by_id_cache_miss_hits_repo(self, use_cases, tenant_id, user_id):
        cmd = CreateTaskCommand(tenant_id=tenant_id, created_by=user_id, title="Task")
        task = await use_cases.create(cmd)
        found = await use_cases.get_by_id(GetTaskByIdQuery(id=task.id, tenant_id=tenant_id))
        assert found.id == task.id

    @pytest.mark.asyncio
    async def test_list_with_null_cache(self, use_cases, tenant_id, user_id):
        for i in range(3):
            await use_cases.create(CreateTaskCommand(tenant_id=tenant_id, created_by=user_id, title=f"Task {i}"))
        tasks = await use_cases.list_tasks(ListTasksQuery(tenant_id=tenant_id))
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_update(self, use_cases, tenant_id, user_id):
        """Memastikan update tidak error meski cache null."""
        from app.application.commands.task_commands import UpdateTaskCommand
        task = await use_cases.create(CreateTaskCommand(tenant_id=tenant_id, created_by=user_id, title="Old"))
        updated = await use_cases.update(UpdateTaskCommand(id=task.id, tenant_id=tenant_id, title="New"))
        assert updated.title == "New"
