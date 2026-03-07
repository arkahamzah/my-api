from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.role import Role
from app.infrastructure.database.models.user import UserModel


def _to_entity(m: UserModel) -> User:
    return User(
        id=m.id, email=m.email, username=m.username,
        hashed_password=m.hashed_password, role=Role(m.role),
        is_active=m.is_active, tenant_id=m.tenant_id,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _to_model(e: User) -> UserModel:
    return UserModel(
        id=e.id, email=e.email, username=e.username,
        hashed_password=e.hashed_password, role=e.role.value,
        is_active=e.is_active, tenant_id=e.tenant_id,
        created_at=e.created_at, updated_at=e.updated_at,
    )


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: User) -> User:
        model = _to_model(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, user_id: UUID, tenant_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == tenant_id))
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_email(self, email: str, tenant_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email, UserModel.tenant_id == tenant_id))
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_username(self, username: str, tenant_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username, UserModel.tenant_id == tenant_id))
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id, UserModel.tenant_id == user.tenant_id))
        model = result.scalar_one()
        model.email = user.email
        model.username = user.username
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.is_active = user.is_active
        model.updated_at = user.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, tenant_id: str) -> bool:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == tenant_id))
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def list_by_tenant(self, tenant_id: str, limit: int = 20, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.tenant_id == tenant_id)
            .order_by(UserModel.created_at.desc()).limit(limit).offset(offset))
        return [_to_entity(m) for m in result.scalars().all()]
