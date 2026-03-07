from abc import abstractmethod
from uuid import UUID
from app.domain.entities.task import Task, TaskStatus
from app.domain.repositories.base import BaseRepository

class TaskRepository(BaseRepository[Task]):
    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID, status: TaskStatus | None = None, skip: int = 0, limit: int = 20) -> list[Task]: ...
    @abstractmethod
    async def count_by_tenant(self, tenant_id: UUID) -> int: ...
