from abc import abstractmethod
from uuid import UUID
from app.domain.entities.tenant import Tenant
from app.domain.repositories.base import BaseRepository

class TenantRepository(BaseRepository[Tenant]):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Tenant | None: ...
    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 20) -> list[Tenant]: ...
    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool: ...
