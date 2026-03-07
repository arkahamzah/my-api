"""
Tenant Schemas - demonstrasi advanced Pydantic v2.
"""
import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampMixin

# ── Type Aliases dengan Annotated (Pydantic v2 style) ────────────────────────
TenantSlug = Annotated[
    str,
    Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Slug unik tenant (huruf kecil, angka, dan tanda hubung)",
        examples=["acme-corp", "startup123"],
    ),
]

TenantPlan = Literal["free", "pro", "enterprise"]


# ── Request Schemas ───────────────────────────────────────────────────────────
class TenantCreate(BaseSchema):
    """Schema untuk membuat tenant baru."""
    name: Annotated[str, Field(min_length=2, max_length=100)]
    slug: TenantSlug
    plan: TenantPlan = "free"
    owner_email: Annotated[str, Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")]
    max_members: Annotated[int, Field(ge=1, le=1000)] = 5

    # Pydantic v2: @field_validator menggantikan @validator
    # mode='before': jalan sebelum type conversion (raw value)
    # mode='after': jalan setelah type conversion (sudah typed)
    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        """Auto-normalize slug ke lowercase."""
        return v.lower().strip()

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Nama tidak boleh mengandung karakter berbahaya."""
        if re.search(r"[<>\"'&]", v):
            raise ValueError("Nama mengandung karakter yang tidak diizinkan")
        return v

    # Pydantic v2: @model_validator menggantikan @root_validator
    # mode='after': semua field sudah tervalidasi, self adalah instance
    @model_validator(mode="after")
    def validate_plan_limits(self) -> "TenantCreate":
        """Validasi cross-field: plan vs max_members."""
        limits = {"free": 5, "pro": 50, "enterprise": 1000}
        plan_limit = limits[self.plan]
        if self.max_members > plan_limit:
            raise ValueError(
                f"Plan '{self.plan}' hanya mendukung maksimal {plan_limit} member, "
                f"bukan {self.max_members}"
            )
        return self


class TenantUpdate(BaseSchema):
    """Schema untuk update tenant. Semua field opsional."""
    name: Annotated[str, Field(min_length=2, max_length=100)] | None = None
    plan: TenantPlan | None = None
    max_members: Annotated[int, Field(ge=1, le=1000)] | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TenantUpdate":
        """Pastikan minimal satu field diisi."""
        values = {k: v for k, v in self.model_dump().items() if v is not None}
        if not values:
            raise ValueError("Minimal satu field harus diisi untuk update")
        return self


# ── Response Schemas ──────────────────────────────────────────────────────────
class TenantResponse(BaseSchema, TimestampMixin):
    """Schema response tenant (dari ORM object)."""
    id: UUID
    name: str
    slug: str
    plan: TenantPlan
    is_active: bool
    max_members: int
    member_count: int = 0

    # Pydantic v2: model_config from_attributes=True sudah di BaseSchema
    # Tidak perlu orm_mode = True lagi


class TenantSummary(BaseSchema):
    """Schema ringkasan tenant (untuk list)."""
    id: UUID
    name: str
    slug: str
    plan: TenantPlan
    is_active: bool
