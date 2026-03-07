"""
Task Schemas - Pydantic v2 dengan complex validation.
"""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampMixin

TaskStatus = Literal["todo", "in_progress", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


class TaskCreate(BaseSchema):
    title: Annotated[str, Field(min_length=3, max_length=255)]
    description: Annotated[str, Field(max_length=5000)] | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    tags: list[Annotated[str, Field(min_length=1, max_length=50)]] = Field(default_factory=list)

    @field_validator("tags", mode="after")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("Maksimal 10 tags per task")
        # Deduplicate dan lowercase
        return list({tag.lower() for tag in v})

    @model_validator(mode="after")
    def validate_due_date(self) -> "TaskCreate":
        if self.due_date and self.due_date < datetime.now(tz=self.due_date.tzinfo):
            raise ValueError("Due date tidak boleh di masa lalu")
        return self


class TaskUpdate(BaseSchema):
    title: Annotated[str, Field(min_length=3, max_length=255)] | None = None
    description: Annotated[str, Field(max_length=5000)] | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    tags: list[Annotated[str, Field(min_length=1, max_length=50)]] | None = None


class TaskStatusUpdate(BaseSchema):
    """Dedicated schema untuk update status saja."""
    status: TaskStatus
    comment: Annotated[str, Field(max_length=500)] | None = None

    @model_validator(mode="after")
    def require_comment_for_cancel(self) -> "TaskStatusUpdate":
        if self.status == "cancelled" and not self.comment:
            raise ValueError("Alasan pembatalan (comment) wajib diisi")
        return self


class TaskResponse(BaseSchema, TimestampMixin):
    id: UUID
    tenant_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    assignee_id: UUID | None
    tags: list[str]
    created_by: UUID

    # Pydantic v2: model_serializer untuk custom serialisasi
    def model_post_init(self, __context: object) -> None:
        """Hook setelah init - bisa dipakai untuk post-processing."""
        pass


class TaskSummary(BaseSchema):
    """Ringkasan task untuk list view."""
    id: UUID
    title: str
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    assignee_id: UUID | None
