from dataclasses import dataclass
from uuid import UUID

from app.domain.value_objects.role import Role


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    username: str
    password: str
    tenant_id: str
    role: Role = Role.MEMBER

@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str
    tenant_id: str

@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str

@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: UUID
    tenant_id: str
    current_password: str
    new_password: str

@dataclass(frozen=True)
class ChangeRoleCommand:
    target_user_id: UUID
    tenant_id: str
    new_role: Role
    requested_by: UUID

@dataclass(frozen=True)
class GetUserByIdQuery:
    user_id: UUID
    tenant_id: str

@dataclass(frozen=True)
class ListUsersQuery:
    tenant_id: str
    limit: int = 20
    offset: int = 0
