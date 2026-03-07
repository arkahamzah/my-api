"""
Task Use Cases - Phase 3: dengan caching + background tasks.
"""
import dataclasses
from datetime import datetime
from uuid import uuid4

from app.application.background.audit_tasks import log_task_created, log_task_status_changed
from app.application.commands.task_commands import (
    CreateTaskCommand, DeleteTaskCommand, UpdateTaskCommand, UpdateTaskStatusCommand,
)
from app.application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from app.application.services.cache_service import CacheKeys, CacheService, NullCacheService
from app.core.exceptions import ForbiddenError, NotFoundError
from app.domain.entities.task import Task
from app.domain.repositories.task_repository import TaskRepository

TASK_TTL = 120   # 2 menit
LIST_TTL = 60    # 1 menit


class TaskUseCases:
    def __init__(self, repo: TaskRepository, cache: CacheService | None = None) -> None:
        self.repo = repo
        self.cache = cache or NullCacheService()

    async def create(self, cmd: CreateTaskCommand) -> Task:
        task = Task(
            id=uuid4(), tenant_id=cmd.tenant_id, created_by=cmd.created_by,
            title=cmd.title, description=cmd.description, status=cmd.status,
            priority=cmd.priority, due_date=cmd.due_date, assignee_id=cmd.assignee_id,
            tags=list(cmd.tags),
        )
        saved = await self.repo.save(task)
        await self.cache.delete_pattern(CacheKeys.tenant_tasks_pattern(str(cmd.tenant_id)))
        # Background audit (fire & forget)
        import asyncio
        asyncio.create_task(log_task_created(saved.id, saved.tenant_id, saved.created_by, saved.title))
        return saved

    async def update(self, cmd: UpdateTaskCommand) -> Task:
        task = await self._get_and_verify(cmd.id, cmd.tenant_id)
        if cmd.title is not None: task.title = cmd.title
        if cmd.description is not None: task.description = cmd.description
        if cmd.status is not None: task.status = cmd.status
        if cmd.priority is not None: task.priority = cmd.priority
        if cmd.due_date is not None: task.due_date = cmd.due_date
        if cmd.assignee_id is not None: task.assignee_id = cmd.assignee_id
        if cmd.tags is not None: task.tags = list(cmd.tags)
        task.updated_at = datetime.utcnow()
        saved = await self.repo.save(task)
        await self.cache.delete(CacheKeys.task(str(cmd.id)))
        await self.cache.delete_pattern(CacheKeys.tenant_tasks_pattern(str(cmd.tenant_id)))
        return saved

    async def update_status(self, cmd: UpdateTaskStatusCommand) -> Task:
        task = await self._get_and_verify(cmd.id, cmd.tenant_id)
        old_status = task.status
        task.update_status(cmd.status)
        saved = await self.repo.save(task)
        await self.cache.delete(CacheKeys.task(str(cmd.id)))
        await self.cache.delete_pattern(CacheKeys.tenant_tasks_pattern(str(cmd.tenant_id)))
        import asyncio
        asyncio.create_task(log_task_status_changed(saved.id, saved.tenant_id, old_status, cmd.status))
        return saved

    async def delete(self, cmd: DeleteTaskCommand) -> bool:
        await self._get_and_verify(cmd.id, cmd.tenant_id)
        result = await self.repo.delete(cmd.id)
        await self.cache.delete(CacheKeys.task(str(cmd.id)))
        await self.cache.delete_pattern(CacheKeys.tenant_tasks_pattern(str(cmd.tenant_id)))
        return result

    async def get_by_id(self, query: GetTaskByIdQuery) -> Task:
        key = CacheKeys.task(str(query.id))
        cached = await self.cache.get(key)
        if cached:
            return Task(**{k: v for k, v in cached.items()})
        task = await self._get_and_verify(query.id, query.tenant_id)
        await self.cache.set(key, dataclasses.asdict(task), ttl=TASK_TTL)
        return task

    async def list_tasks(self, query: ListTasksQuery) -> list[Task]:
        key = CacheKeys.task_list(str(query.tenant_id), query.status, query.skip, query.limit)
        cached = await self.cache.get(key)
        if cached:
            return [Task(**item) for item in cached]
        tasks = await self.repo.get_by_tenant(
            tenant_id=query.tenant_id, status=query.status, skip=query.skip, limit=query.limit,
        )
        await self.cache.set(key, [dataclasses.asdict(t) for t in tasks], ttl=LIST_TTL)
        return tasks

    async def _get_and_verify(self, task_id, tenant_id) -> Task:
        task = await self.repo.get_by_id(task_id)
        if not task: raise NotFoundError("Task", task_id)
        if task.tenant_id != tenant_id: raise ForbiddenError("Task tidak ada di tenant ini")
        return task
