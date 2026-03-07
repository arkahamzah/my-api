from uuid import UUID
from app.domain.entities.task import Task, TaskStatus
from app.domain.entities.tenant import Tenant
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.tenant_repository import TenantRepository

class InMemoryTaskRepo(TaskRepository):
    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    async def get_by_id(self, id: UUID) -> Task | None:
        return self._store.get(str(id))

    async def get_by_tenant(self, tenant_id: UUID, status: TaskStatus | None = None, skip: int = 0, limit: int = 20) -> list[Task]:
        tasks = [t for t in self._store.values() if t.tenant_id == tenant_id]
        if status: tasks = [t for t in tasks if t.status == status]
        return tasks[skip:skip+limit]

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        return sum(1 for t in self._store.values() if t.tenant_id == tenant_id)

    async def save(self, entity: Task) -> Task:
        self._store[str(entity.id)] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        key = str(id)
        if key not in self._store: return False
        del self._store[key]; return True

class InMemoryTenantRepo(TenantRepository):
    def __init__(self) -> None:
        self._store: dict[str, Tenant] = {}

    async def get_by_id(self, id: UUID) -> Tenant | None:
        return self._store.get(str(id))

    async def get_by_slug(self, slug: str) -> Tenant | None:
        return next((t for t in self._store.values() if t.slug == slug), None)

    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Tenant]:
        return list(self._store.values())[skip:skip+limit]

    async def exists_by_slug(self, slug: str) -> bool:
        return any(t.slug == slug for t in self._store.values())

    async def save(self, entity: Tenant) -> Tenant:
        self._store[str(entity.id)] = entity; return entity

    async def delete(self, id: UUID) -> bool:
        key = str(id)
        if key not in self._store: return False
        del self._store[key]; return True
