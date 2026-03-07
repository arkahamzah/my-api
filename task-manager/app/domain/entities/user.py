from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.role import Permission, Role, has_permission


@dataclass
class User:
    id: UUID
    email: str
    username: str
    hashed_password: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tenant_id: str

    @classmethod
    def create(
        cls,
        email: str,
        username: str,
        hashed_password: str,
        tenant_id: str,
        role: Role = Role.MEMBER,
    ) -> "User":
        now = datetime.utcnow()
        return cls(
            id=uuid4(), email=email, username=username,
            hashed_password=hashed_password, role=role,
            is_active=True, created_at=now, updated_at=now, tenant_id=tenant_id,
        )

    def has_permission(self, permission: Permission) -> bool:
        return has_permission(self.role, permission)

    def can_manage_task(self, task_owner_id: UUID) -> bool:
        if self.id == task_owner_id:
            return True
        return self.has_permission(Permission.TASK_UPDATE_ALL)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def change_role(self, new_role: Role) -> None:
        self.role = new_role
        self.updated_at = datetime.utcnow()
