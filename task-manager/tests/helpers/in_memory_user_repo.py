"""
In-memory UserRepository untuk integration tests.
Tidak butuh koneksi database nyata.
"""
from uuid import UUID

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


class InMemoryUserRepo(UserRepository):
    def __init__(self):
        self._store: dict[str, User] = {}  # key: f"{tenant_id}:{user_id}"

    def _key(self, user_id: UUID, tenant_id: str) -> str:
        return f"{tenant_id}:{user_id}"

    async def create(self, user: User) -> User:
        self._store[self._key(user.id, user.tenant_id)] = user
        return user

    async def get_by_id(self, user_id: UUID, tenant_id: str) -> User | None:
        return self._store.get(self._key(user_id, tenant_id))

    async def get_by_email(self, email: str, tenant_id: str) -> User | None:
        for user in self._store.values():
            if user.email == email and user.tenant_id == tenant_id:
                return user
        return None

    async def get_by_username(self, username: str, tenant_id: str) -> User | None:
        for user in self._store.values():
            if user.username == username and user.tenant_id == tenant_id:
                return user
        return None

    async def update(self, user: User) -> User:
        self._store[self._key(user.id, user.tenant_id)] = user
        return user

    async def delete(self, user_id: UUID, tenant_id: str) -> bool:
        key = self._key(user_id, tenant_id)
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 20, offset: int = 0
    ) -> list[User]:
        users = [u for u in self._store.values() if u.tenant_id == tenant_id]
        users.sort(key=lambda u: u.created_at, reverse=True)
        return users[offset : offset + limit]
