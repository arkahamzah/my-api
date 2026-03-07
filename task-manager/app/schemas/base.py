"""
Pydantic v2 Schemas - demonstrasi fitur-fitur baru.

Key differences Pydantic v2 vs v1:
- model_config dict (bukan class Config)
- field_validator mengganti @validator
- model_validator mengganti @root_validator
- model_dump() mengganti .dict()
- model_validate() mengganti .parse_obj()
- ConfigDict dari pydantic import
"""
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """
    Base schema dengan konfigurasi default.
    Pydantic v2: pakai ConfigDict, bukan class Config.
    """
    model_config = ConfigDict(
        # Populate model dari ORM objects (mengganti orm_mode = True)
        from_attributes=True,
        # Validasi assignment setelah init
        validate_assignment=True,
        # Strip whitespace dari str
        str_strip_whitespace=True,
        # Populate by name atau alias
        populate_by_name=True,
        # Serialisasi by alias default
        serialize_by_alias=False,
    )


class TimestampMixin(BaseModel):
    """Mixin untuk timestamp fields."""
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseSchema):
    """Query params untuk pagination."""
    page: Annotated[int, Field(default=1, ge=1, description="Halaman ke-")]
    page_size: Annotated[int, Field(default=20, ge=1, le=100, description="Jumlah item per halaman")]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema):
    """Generic paginated response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[Any],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse":
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        )


class ErrorResponse(BaseSchema):
    """Standard error response."""
    error_code: str
    message: str
    detail: Any = None


class SuccessResponse(BaseSchema):
    """Standard success response."""
    message: str = "Berhasil"
    data: Any = None
