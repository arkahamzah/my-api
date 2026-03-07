"""
Tests untuk schemas Pydantic v2.

Jalankan dengan: pytest tests/ -v
"""
import pytest
from pydantic import ValidationError

from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.task import TaskCreate, TaskStatusUpdate


class TestTenantCreate:
    """Test TenantCreate schema dengan Pydantic v2 validation."""

    def test_valid_tenant(self):
        tenant = TenantCreate(
            name="Acme Corp",
            slug="acme-corp",
            plan="pro",
            owner_email="owner@acme.com",
            max_members=50,
        )
        assert tenant.slug == "acme-corp"
        assert tenant.plan == "pro"

    def test_slug_auto_lowercase(self):
        """@field_validator normalize slug ke lowercase."""
        tenant = TenantCreate(
            name="Test",
            slug="UPPER-CASE",
            owner_email="test@test.com",
        )
        assert tenant.slug == "upper-case"

    def test_invalid_slug_format(self):
        """Slug dengan karakter invalid harus gagal."""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Test",
                slug="invalid slug!",  # spasi dan ! tidak valid
                owner_email="test@test.com",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("slug",) for e in errors)

    def test_plan_member_limit_cross_validation(self):
        """@model_validator: plan free tidak boleh > 5 members."""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Test",
                slug="test-tenant",
                plan="free",
                owner_email="test@test.com",
                max_members=50,  # free limit = 5
            )
        error_str = str(exc_info.value)
        assert "free" in error_str
        assert "5" in error_str

    def test_pydantic_v2_model_dump(self):
        """model_dump() menggantikan .dict() di Pydantic v2."""
        tenant = TenantCreate(
            name="Test Co",
            slug="test-co",
            owner_email="test@test.com",
        )
        data = tenant.model_dump()
        assert isinstance(data, dict)
        assert data["slug"] == "test-co"
        assert data["plan"] == "free"

    def test_pydantic_v2_model_dump_exclude_none(self):
        """model_dump(exclude_none=True) untuk partial update."""
        update = TenantUpdate(name="New Name")
        data = update.model_dump(exclude_none=True)
        assert data == {"name": "New Name"}
        assert "plan" not in data
        assert "is_active" not in data


class TestTenantUpdate:
    def test_empty_update_fails(self):
        """@model_validator: minimal satu field harus diisi."""
        with pytest.raises(ValidationError):
            TenantUpdate()  # semua None


class TestTaskStatusUpdate:
    def test_cancel_requires_comment(self):
        """@model_validator: cancel task harus ada comment."""
        with pytest.raises(ValidationError) as exc_info:
            TaskStatusUpdate(status="cancelled")  # tidak ada comment
        assert "comment" in str(exc_info.value).lower() or "cancel" in str(exc_info.value).lower()

    def test_cancel_with_comment_valid(self):
        update = TaskStatusUpdate(status="cancelled", comment="Tidak relevan lagi")
        assert update.status == "cancelled"
        assert update.comment is not None

    def test_other_status_no_comment_needed(self):
        update = TaskStatusUpdate(status="done")
        assert update.status == "done"


class TestTaskCreate:
    def test_tags_deduplication(self):
        """@field_validator dedup tags."""
        task = TaskCreate(
            title="Test Task",
            tags=["python", "PYTHON", "fastapi", "fastapi"],
        )
        assert len(task.tags) == 2  # deduplicated dan lowercase
        assert "python" in task.tags
        assert "fastapi" in task.tags

    def test_too_many_tags(self):
        with pytest.raises(ValidationError):
            TaskCreate(
                title="Test Task",
                tags=[f"tag{i}" for i in range(11)],  # 11 tags, max 10
            )

    def test_pydantic_v2_model_validate(self):
        """model_validate() menggantikan parse_obj() di Pydantic v2."""
        data = {"title": "Test Task", "priority": "high"}
        task = TaskCreate.model_validate(data)
        assert task.title == "Test Task"
        assert task.priority == "high"
        assert task.status == "todo"  # default value
