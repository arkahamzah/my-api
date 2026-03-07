from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.task import Task, TaskStatus
from app.domain.repositories.task_repository import TaskRepository
from app.infrastructure.database.models.task import TaskModel

class SQLAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(m: TaskModel) -> Task:
        return Task(id=m.id, tenant_id=m.tenant_id, title=m.title, description=m.description,
            status=m.status, priority=m.priority, due_date=m.due_date, assignee_id=m.assignee_id,
            tags=list(m.tags or []), created_by=m.created_by, created_at=m.created_at, updated_at=m.updated_at)

    async def get_by_id(self, id: UUID) -> Task | None:
        m = await self._session.get(TaskModel, id)
        return self._to_entity(m) if m else None

    async def get_by_tenant(self, tenant_id: UUID, status: TaskStatus | None = None, skip: int = 0, limit: int = 20) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.tenant_id == tenant_id)
        if status: stmt = stmt.where(TaskModel.status == status)
        stmt = stmt.order_by(TaskModel.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        result = await self._session.execute(select(func.count()).where(TaskModel.tenant_id == tenant_id))
        return result.scalar_one()

    async def save(self, entity: Task) -> Task:
        m = await self._session.get(TaskModel, entity.id)
        if m is None:
            m = TaskModel(id=entity.id, tenant_id=entity.tenant_id, title=entity.title,
                description=entity.description, status=entity.status, priority=entity.priority,
                due_date=entity.due_date, assignee_id=entity.assignee_id, tags=entity.tags,
                created_by=entity.created_by, created_at=entity.created_at, updated_at=entity.updated_at)
            self._session.add(m)
        else:
            m.title = entity.title; m.description = entity.description; m.status = entity.status
            m.priority = entity.priority; m.due_date = entity.due_date
            m.assignee_id = entity.assignee_id; m.tags = entity.tags; m.updated_at = entity.updated_at
        await self._session.flush()
        return entity

    async def delete(self, id: UUID) -> bool:
        m = await self._session.get(TaskModel, id)
        if m is None: return False
        await self._session.delete(m)
        await self._session.flush()
        return True
