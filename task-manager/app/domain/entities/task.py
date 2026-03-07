from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

TaskStatus = Literal["todo", "in_progress", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]

@dataclass
class Task:
    tenant_id: UUID
    title: str
    created_by: UUID
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update_status(self, new_status: TaskStatus) -> None:
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date.replace(tzinfo=None)
