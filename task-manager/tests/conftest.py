from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.services.cache_service import NullCacheService
from app.application.use_cases.task_use_cases import TaskUseCases
from app.application.use_cases.tenant_use_cases import TenantUseCases
from app.core.dependencies import get_current_user, get_task_use_cases, get_tenant_use_cases
from app.domain.entities.user import User
from app.domain.value_objects.role import Role
from app.main import app
from tests.helpers.in_memory_repos import InMemoryTaskRepo, InMemoryTenantRepo


def _mock_admin_user() -> User:
    now = datetime.utcnow()
    return User(
        id=uuid4(), email="admin@test.com", username="admin",
        hashed_password="", role=Role.ADMIN, is_active=True,
        created_at=now, updated_at=now, tenant_id="test",
    )


@pytest.fixture(autouse=True)
def override_use_cases():
    task_repo = InMemoryTaskRepo()
    tenant_repo = InMemoryTenantRepo()
    app.dependency_overrides[get_task_use_cases] = lambda: TaskUseCases(task_repo, NullCacheService())
    app.dependency_overrides[get_tenant_use_cases] = lambda: TenantUseCases(tenant_repo, NullCacheService())
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    # Override get_current_user HANYA untuk sync client (test_endpoints.py)
    app.dependency_overrides[get_current_user] = _mock_admin_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)