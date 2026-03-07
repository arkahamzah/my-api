"""
Generic pagination response wrapper.
"""
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_next: bool

    @classmethod
    def create(cls, items: list[T], total: int, skip: int, limit: int) -> "PaginatedResponse[T]":
        return cls(items=items, total=total, skip=skip, limit=limit, has_next=skip + limit < total)
