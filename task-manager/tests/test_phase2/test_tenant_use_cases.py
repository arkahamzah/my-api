import pytest
from uuid import uuid4
from app.application.commands.tenant_commands import CreateTenantCommand, UpdateTenantCommand, DeleteTenantCommand
from app.application.queries.tenant_queries import GetTenantByIdQuery, GetTenantBySlugQuery, ListTenantsQuery
from app.application.use_cases.tenant_use_cases import TenantUseCases
from app.core.exceptions import ConflictError, NotFoundError
from tests.helpers.in_memory_repos import InMemoryTenantRepo

@pytest.fixture
def use_cases(): return TenantUseCases(InMemoryTenantRepo())

def _cmd(**kw):
    d = dict(name="Acme", slug="acme-corp", owner_email="owner@acme.com"); d.update(kw)
    return CreateTenantCommand(**d)

class TestCreateTenant:
    @pytest.mark.asyncio
    async def test_basic(self, use_cases):
        t = await use_cases.create(_cmd())
        assert t.slug == "acme-corp" and t.plan == "free" and t.is_active is True

    @pytest.mark.asyncio
    async def test_duplicate_slug_raises_conflict(self, use_cases):
        await use_cases.create(_cmd())
        with pytest.raises(ConflictError):
            await use_cases.create(_cmd())

    @pytest.mark.asyncio
    async def test_pro_plan(self, use_cases):
        t = await use_cases.create(_cmd(plan="pro", max_members=50))
        assert t.plan == "pro" and t.max_members == 50

class TestGetTenant:
    @pytest.mark.asyncio
    async def test_get_by_id(self, use_cases):
        t = await use_cases.create(_cmd())
        assert (await use_cases.get_by_id(GetTenantByIdQuery(id=t.id))).id == t.id

    @pytest.mark.asyncio
    async def test_nonexistent_raises_notfound(self, use_cases):
        with pytest.raises(NotFoundError):
            await use_cases.get_by_id(GetTenantByIdQuery(id=uuid4()))

    @pytest.mark.asyncio
    async def test_get_by_slug(self, use_cases):
        await use_cases.create(_cmd(slug="my-co"))
        assert (await use_cases.get_by_slug(GetTenantBySlugQuery(slug="my-co"))).slug == "my-co"

class TestUpdateTenant:
    @pytest.mark.asyncio
    async def test_update_name(self, use_cases):
        t = await use_cases.create(_cmd())
        u = await use_cases.update(UpdateTenantCommand(id=t.id, name="New Name"))
        assert u.name == "New Name"

    @pytest.mark.asyncio
    async def test_upgrade_plan(self, use_cases):
        t = await use_cases.create(_cmd())
        u = await use_cases.update(UpdateTenantCommand(id=t.id, plan="pro"))
        assert u.plan == "pro" and u.max_members == 50

    @pytest.mark.asyncio
    async def test_upgrade_enterprise(self, use_cases):
        t = await use_cases.create(_cmd())
        u = await use_cases.update(UpdateTenantCommand(id=t.id, plan="enterprise"))
        assert u.max_members == 1000

    @pytest.mark.asyncio
    async def test_deactivate(self, use_cases):
        t = await use_cases.create(_cmd())
        u = await use_cases.update(UpdateTenantCommand(id=t.id, is_active=False))
        assert u.is_active is False

class TestListTenants:
    @pytest.mark.asyncio
    async def test_list_all(self, use_cases):
        for i in range(3): await use_cases.create(_cmd(slug=f"t{i}"))
        assert len(await use_cases.list_tenants(ListTenantsQuery())) == 3

    @pytest.mark.asyncio
    async def test_pagination(self, use_cases):
        for i in range(5): await use_cases.create(_cmd(slug=f"t{i}"))
        p1 = await use_cases.list_tenants(ListTenantsQuery(skip=0, limit=3))
        p2 = await use_cases.list_tenants(ListTenantsQuery(skip=3, limit=3))
        assert len(p1) == 3 and len(p2) == 2

class TestDeleteTenant:
    @pytest.mark.asyncio
    async def test_delete(self, use_cases):
        t = await use_cases.create(_cmd())
        assert await use_cases.delete(DeleteTenantCommand(id=t.id)) is True

    @pytest.mark.asyncio
    async def test_nonexistent_raises_notfound(self, use_cases):
        with pytest.raises(NotFoundError):
            await use_cases.delete(DeleteTenantCommand(id=uuid4()))
