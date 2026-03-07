from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Query, status
from app.application.commands.task_commands import (
    CreateTaskCommand, DeleteTaskCommand, UpdateTaskCommand, UpdateTaskStatusCommand,
)
from app.application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from app.core.dependencies import TaskUseCasesDep, require_permission
from app.domain.entities.task import Task
from app.domain.entities.user import User
from app.domain.value_objects.role import Permission
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusUpdate, TaskSummary, TaskUpdate

router = APIRouter(prefix="/tenants/{tenant_id}/tasks", tags=["tasks"])


def _to_response(task: Task) -> TaskResponse:
    return TaskResponse.model_validate(vars(task))


@router.get("", response_model=list[TaskSummary])
async def list_tasks(
    tenant_id: UUID,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_READ),
    task_status: Literal["todo", "in_progress", "review", "done", "cancelled"] | None = Query(
        None, alias="status"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[TaskSummary]:
    tasks = await use_cases.list_tasks(
        ListTasksQuery(tenant_id=tenant_id, status=task_status, skip=skip, limit=limit)
    )
    return [TaskSummary.model_validate(vars(t)) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    tenant_id: UUID,
    body: TaskCreate,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_CREATE),
) -> TaskResponse:
    data = body.model_dump()
    cmd = CreateTaskCommand(
        tenant_id=tenant_id,
        created_by=current_user.id,
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "todo"),
        priority=data.get("priority", "medium"),
        due_date=data.get("due_date"),
        assignee_id=data.get("assignee_id"),
        tags=tuple(data.get("tags", [])),
    )
    return _to_response(await use_cases.create(cmd))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    tenant_id: UUID,
    task_id: UUID,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_READ),
) -> TaskResponse:
    return _to_response(await use_cases.get_by_id(GetTaskByIdQuery(id=task_id, tenant_id=tenant_id)))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    tenant_id: UUID,
    task_id: UUID,
    body: TaskUpdate,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_UPDATE),
) -> TaskResponse:
    data = body.model_dump(exclude_none=True)
    cmd = UpdateTaskCommand(
        id=task_id,
        tenant_id=tenant_id,
        title=data.get("title"),
        description=data.get("description"),
        status=data.get("status"),
        priority=data.get("priority"),
        due_date=data.get("due_date"),
        assignee_id=data.get("assignee_id"),
        tags=tuple(data["tags"]) if "tags" in data else None,
    )
    return _to_response(await use_cases.update(cmd))


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    tenant_id: UUID,
    task_id: UUID,
    body: TaskStatusUpdate,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_UPDATE),
) -> TaskResponse:
    return _to_response(
        await use_cases.update_status(
            UpdateTaskStatusCommand(
                id=task_id, tenant_id=tenant_id, status=body.status, comment=body.comment
            )
        )
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    tenant_id: UUID,
    task_id: UUID,
    use_cases: TaskUseCasesDep,
    current_user: User = require_permission(Permission.TASK_DELETE),
) -> None:
    await use_cases.delete(DeleteTaskCommand(id=task_id, tenant_id=tenant_id))