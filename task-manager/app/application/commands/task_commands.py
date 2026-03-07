from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

TaskStatus = Literal["todo", "in_progress", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]

@dataclass(frozen=True)
class CreateTaskCommand:
    tenant_id: UUID
    created_by: UUID
    title: str
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class UpdateTaskCommand:
    id: UUID
    tenant_id: UUID
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    tags: tuple[str, ...] | None = None

@dataclass(frozen=True)
class UpdateTaskStatusCommand:
    id: UUID
    tenant_id: UUID
    status: TaskStatus
    comment: str | None = None

@dataclass(frozen=True)
class DeleteTaskCommand:
    id: UUID
    tenant_id: UUID
