from uuid import UUID
from fastapi import APIRouter, Query, status
from app.application.commands.tenant_commands import (
    CreateTenantCommand, DeleteTenantCommand, UpdateTenantCommand,
)
from app.application.queries.tenant_queries import (
    GetTenantByIdQuery, GetTenantBySlugQuery, ListTenantsQuery,
)
from app.core.dependencies import TenantUseCasesDep, require_permission
from app.domain.entities.tenant import Tenant
from app.domain.entities.user import User
from app.domain.value_objects.role import Permission
from app.schemas.tenant import TenantCreate, TenantResponse, TenantSummary, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _to_response(tenant: Tenant) -> TenantResponse:
    return TenantResponse.model_validate(vars(tenant))


@router.get("", response_model=list[TenantSummary])
async def list_tenants(
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.ADMIN_PANEL),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[TenantSummary]:
    tenants = await use_cases.list_tenants(ListTenantsQuery(skip=skip, limit=limit))
    return [TenantSummary.model_validate(vars(t)) for t in tenants]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.ADMIN_PANEL),
) -> TenantResponse:
    data = body.model_dump()
    return _to_response(
        await use_cases.create(
            CreateTenantCommand(
                name=data["name"],
                slug=data["slug"],
                owner_email=data["owner_email"],
                plan=data.get("plan", "free"),
                max_members=data.get("max_members", 5),
            )
        )
    )


# PENTING: /slug/{slug} harus SEBELUM /{tenant_id} agar tidak tertangkap duluan
@router.get("/slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.USER_READ),
) -> TenantResponse:
    return _to_response(await use_cases.get_by_slug(GetTenantBySlugQuery(slug=slug)))


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.USER_READ),
) -> TenantResponse:
    return _to_response(await use_cases.get_by_id(GetTenantByIdQuery(id=tenant_id)))


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.ADMIN_PANEL),
) -> TenantResponse:
    data = body.model_dump(exclude_none=True)
    return _to_response(
        await use_cases.update(
            UpdateTenantCommand(
                id=tenant_id,
                name=data.get("name"),
                plan=data.get("plan"),
                max_members=data.get("max_members"),
                is_active=data.get("is_active"),
            )
        )
    )


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    use_cases: TenantUseCasesDep,
    current_user: User = require_permission(Permission.ADMIN_PANEL),
) -> None:
    await use_cases.delete(DeleteTenantCommand(id=tenant_id))