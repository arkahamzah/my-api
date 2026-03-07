from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class GetTenantByIdQuery:
    id: UUID

@dataclass(frozen=True)
class GetTenantBySlugQuery:
    slug: str

@dataclass(frozen=True)
class ListTenantsQuery:
    skip: int = 0
    limit: int = 20
