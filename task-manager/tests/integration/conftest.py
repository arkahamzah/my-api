import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.application.services.cache_service import NullCacheService
from app.application.use_cases.task_use_cases import TaskUseCases
from app.application.use_cases.tenant_use_cases import TenantUseCases
from app.core.dependencies import get_task_use_cases, get_tenant_use_cases, get_user_repository
from app.domain.value_objects.role import Role
from app.main import app
from tests.helpers.in_memory_repos import InMemoryTaskRepo, InMemoryTenantRepo
from tests.helpers.in_memory_user_repo import InMemoryUserRepo

TENANT_ID = "tenant-test-001"
BASE_URL = "http://test"


@pytest.fixture
def user_repo() -> InMemoryUserRepo:
    return InMemoryUserRepo()


@pytest.fixture
def task_repo() -> InMemoryTaskRepo:
    return InMemoryTaskRepo()


@pytest.fixture
def tenant_repo() -> InMemoryTenantRepo:
    return InMemoryTenantRepo()


@pytest_asyncio.fixture
async def client(
    user_repo: InMemoryUserRepo,
    task_repo: InMemoryTaskRepo,
    tenant_repo: InMemoryTenantRepo,
) -> AsyncClient:
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_task_use_cases] = lambda: TaskUseCases(
        task_repo, NullCacheService()
    )
    app.dependency_overrides[get_tenant_use_cases] = lambda: TenantUseCases(
        tenant_repo, NullCacheService()
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Auth fixtures (existing, tidak berubah) ───────────────────────────────────

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    payload = {"email": "user@example.com", "username": "testuser", "password": "password123"}
    resp = await client.post(
        "/api/v1/auth/register", json=payload, headers={"X-Tenant-ID": TENANT_ID}
    )
    assert resp.status_code == 201, resp.text
    return {**payload, "data": resp.json()}


@pytest_asyncio.fixture
async def auth_tokens(client: AsyncClient, registered_user: dict) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest_asyncio.fixture
async def auth_headers(auth_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {auth_tokens['access_token']}", "X-Tenant-ID": TENANT_ID}


# ── Role-based header fixtures ────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient, email: str, username: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}


@pytest_asyncio.fixture
async def member_headers(client: AsyncClient) -> dict:
    """MEMBER — role default dari register."""
    return await _register_and_login(client, "member@example.com", "member")


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, user_repo: InMemoryUserRepo) -> dict:
    """ADMIN — register lalu langsung ubah role di InMemoryUserRepo."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "username": "admin", "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    user = await user_repo.get_by_email("admin@example.com", TENANT_ID)
    user.change_role(Role.ADMIN)
    await user_repo.update(user)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}


@pytest_asyncio.fixture
async def viewer_headers(client: AsyncClient, user_repo: InMemoryUserRepo) -> dict:
    """VIEWER — register lalu langsung ubah role di InMemoryUserRepo."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@example.com", "username": "viewer", "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    user = await user_repo.get_by_email("viewer@example.com", TENANT_ID)
    user.change_role(Role.VIEWER)
    await user_repo.update(user)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@example.com", "password": "password123"},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}