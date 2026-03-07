"""
Tests untuk pagination schema.
"""
import pytest
from app.schemas.pagination import PaginatedResponse
from app.schemas.tenant import TenantSummary
from uuid import uuid4


def make_summary(slug: str) -> dict:
    return {"id": str(uuid4()), "name": "Test", "slug": slug, "plan": "free", "is_active": True}


class TestPaginatedResponse:
    def test_has_next_true(self):
        items = [make_summary(f"t{i}") for i in range(3)]
        page = PaginatedResponse[dict].create(items=items, total=10, skip=0, limit=3)
        assert page.has_next is True
        assert page.total == 10

    def test_has_next_false_last_page(self):
        items = [make_summary(f"t{i}") for i in range(2)]
        page = PaginatedResponse[dict].create(items=items, total=5, skip=3, limit=3)
        assert page.has_next is False

    def test_has_next_false_exact_fit(self):
        items = [make_summary(f"t{i}") for i in range(3)]
        page = PaginatedResponse[dict].create(items=items, total=3, skip=0, limit=3)
        assert page.has_next is False

    def test_empty_page(self):
        page = PaginatedResponse[dict].create(items=[], total=0, skip=0, limit=20)
        assert page.items == []
        assert page.has_next is False
        assert page.total == 0

    def test_second_page(self):
        items = [make_summary(f"t{i}") for i in range(3)]
        page = PaginatedResponse[dict].create(items=items, total=8, skip=3, limit=3)
        assert page.has_next is True
        assert page.skip == 3

    def test_items_preserved(self):
        items = [{"x": 1}, {"x": 2}]
        page = PaginatedResponse[dict].create(items=items, total=2, skip=0, limit=10)
        assert page.items == items
