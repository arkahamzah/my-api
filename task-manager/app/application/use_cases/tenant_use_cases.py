"""
Tenant Use Cases - Phase 3: dengan caching.
"""
import dataclasses
from datetime import datetime
from uuid import uuid4

from app.application.background.audit_tasks import log_tenant_created
from app.application.commands.tenant_commands import (
    CreateTenantCommand, DeleteTenantCommand, UpdateTenantCommand,
)
from app.application.queries.tenant_queries import (
    GetTenantByIdQuery, GetTenantBySlugQuery, ListTenantsQuery,
)
from app.application.services.cache_service import CacheKeys, CacheService, NullCacheService
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.entities.tenant import Tenant
from app.domain.repositories.tenant_repository import TenantRepository

TENANT_TTL = 300  # 5 menit


class TenantUseCases:
    def __init__(self, repo: TenantRepository, cache: CacheService | None = None) -> None:
        self.repo = repo
        self.cache = cache or NullCacheService()

    async def create(self, cmd: CreateTenantCommand) -> Tenant:
        if await self.repo.exists_by_slug(cmd.slug):
            raise ConflictError(f"Slug '{cmd.slug}' sudah digunakan")
        tenant = Tenant(id=uuid4(), name=cmd.name, slug=cmd.slug, owner_email=cmd.owner_email,
            plan=cmd.plan, max_members=cmd.max_members)
        saved = await self.repo.save(tenant)
        await self.cache.delete_pattern("tenant:list:*")
        import asyncio
        asyncio.create_task(log_tenant_created(saved.id, saved.slug, saved.plan))
        return saved

    async def get_by_id(self, query: GetTenantByIdQuery) -> Tenant:
        key = CacheKeys.tenant(str(query.id))
        cached = await self.cache.get(key)
        if cached:
            return Tenant(**cached)
        tenant = await self.repo.get_by_id(query.id)
        if not tenant: raise NotFoundError("Tenant", query.id)
        await self.cache.set(key, dataclasses.asdict(tenant), ttl=TENANT_TTL)
        return tenant

    async def get_by_slug(self, query: GetTenantBySlugQuery) -> Tenant:
        key = CacheKeys.tenant_slug(query.slug)
        cached = await self.cache.get(key)
        if cached:
            return Tenant(**cached)
        tenant = await self.repo.get_by_slug(query.slug)
        if not tenant: raise NotFoundError("Tenant", query.slug)
        await self.cache.set(key, dataclasses.asdict(tenant), ttl=TENANT_TTL)
        return tenant

    async def list_tenants(self, query: ListTenantsQuery) -> list[Tenant]:
        key = CacheKeys.tenant_list(query.skip, query.limit)
        cached = await self.cache.get(key)
        if cached:
            return [Tenant(**item) for item in cached]
        tenants = await self.repo.list_all(skip=query.skip, limit=query.limit)
        await self.cache.set(key, [dataclasses.asdict(t) for t in tenants], ttl=TENANT_TTL)
        return tenants

    async def update(self, cmd: UpdateTenantCommand) -> Tenant:
        tenant = await self.repo.get_by_id(cmd.id)
        if not tenant: raise NotFoundError("Tenant", cmd.id)
        if cmd.name is not None: tenant.name = cmd.name
        if cmd.plan is not None: tenant.upgrade_plan(cmd.plan)
        if cmd.max_members is not None: tenant.max_members = cmd.max_members
        if cmd.is_active is not None: tenant.is_active = cmd.is_active
        tenant.updated_at = datetime.utcnow()
        saved = await self.repo.save(tenant)
        await self.cache.delete(CacheKeys.tenant(str(cmd.id)))
        await self.cache.delete(CacheKeys.tenant_slug(saved.slug))
        await self.cache.delete_pattern("tenant:list:*")
        return saved

    async def delete(self, cmd: DeleteTenantCommand) -> bool:
        tenant = await self.repo.get_by_id(cmd.id)
        if not tenant: raise NotFoundError("Tenant", cmd.id)
        result = await self.repo.delete(cmd.id)
        await self.cache.delete(CacheKeys.tenant(str(cmd.id)))
        await self.cache.delete(CacheKeys.tenant_slug(tenant.slug))
        await self.cache.delete_pattern("tenant:list:*")
        return result
