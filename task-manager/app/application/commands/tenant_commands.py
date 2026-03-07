from dataclasses import dataclass
from typing import Literal
from uuid import UUID

TenantPlan = Literal["free", "pro", "enterprise"]

@dataclass(frozen=True)
class CreateTenantCommand:
    name: str
    slug: str
    owner_email: str
    plan: TenantPlan = "free"
    max_members: int = 5

@dataclass(frozen=True)
class UpdateTenantCommand:
    id: UUID
    name: str | None = None
    plan: TenantPlan | None = None
    max_members: int | None = None
    is_active: bool | None = None

@dataclass(frozen=True)
class DeleteTenantCommand:
    id: UUID
