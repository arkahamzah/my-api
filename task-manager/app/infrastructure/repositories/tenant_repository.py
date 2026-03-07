from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.tenant import Tenant
from app.domain.repositories.tenant_repository import TenantRepository
from app.infrastructure.database.models.tenant import TenantModel

class SQLAlchemyTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(m: TenantModel) -> Tenant:
        return Tenant(id=m.id, name=m.name, slug=m.slug, plan=m.plan, owner_email=m.owner_email,
            is_active=m.is_active, max_members=m.max_members, member_count=m.member_count,
            created_at=m.created_at, updated_at=m.updated_at)

    async def get_by_id(self, id: UUID) -> Tenant | None:
        m = await self._session.get(TenantModel, id)
        return self._to_entity(m) if m else None

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(select(TenantModel).where(TenantModel.slug == slug))
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Tenant]:
        result = await self._session.execute(select(TenantModel).offset(skip).limit(limit))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self._session.execute(select(func.count()).where(TenantModel.slug == slug))
        return result.scalar_one() > 0

    async def save(self, entity: Tenant) -> Tenant:
        m = await self._session.get(TenantModel, entity.id)
        if m is None:
            m = TenantModel(id=entity.id, name=entity.name, slug=entity.slug, plan=entity.plan,
                owner_email=entity.owner_email, is_active=entity.is_active,
                max_members=entity.max_members, member_count=entity.member_count,
                created_at=entity.created_at, updated_at=entity.updated_at)
            self._session.add(m)
        else:
            m.name = entity.name; m.plan = entity.plan; m.is_active = entity.is_active
            m.max_members = entity.max_members; m.member_count = entity.member_count
            m.updated_at = entity.updated_at
        await self._session.flush()
        return entity

    async def delete(self, id: UUID) -> bool:
        m = await self._session.get(TenantModel, id)
        if m is None: return False
        await self._session.delete(m)
        await self._session.flush()
        return True
