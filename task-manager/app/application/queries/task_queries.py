from dataclasses import dataclass
from typing import Literal
from uuid import UUID

TaskStatus = Literal["todo", "in_progress", "review", "done", "cancelled"]

@dataclass(frozen=True)
class GetTaskByIdQuery:
    id: UUID
    tenant_id: UUID

@dataclass(frozen=True)
class ListTasksQuery:
    tenant_id: UUID
    status: TaskStatus | None = None
    skip: int = 0
    limit: int = 20
