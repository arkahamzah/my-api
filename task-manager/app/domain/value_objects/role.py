from enum import Enum


class Permission(str, Enum):
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_READ_ALL = "task:read_all"
    TASK_UPDATE_ALL = "task:update_all"
    TASK_DELETE_ALL = "task:delete_all"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_READ_ALL = "user:read_all"
    USER_UPDATE_ALL = "user:update_all"
    USER_DELETE_ALL = "user:delete_all"
    ADMIN_PANEL = "admin:panel"


class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset([
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE,
        Permission.TASK_DELETE, Permission.TASK_READ_ALL, Permission.TASK_UPDATE_ALL,
        Permission.TASK_DELETE_ALL, Permission.USER_READ, Permission.USER_UPDATE,
        Permission.USER_DELETE, Permission.USER_READ_ALL, Permission.USER_UPDATE_ALL,
        Permission.USER_DELETE_ALL, Permission.ADMIN_PANEL,
    ]),
    Role.MEMBER: frozenset([
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE,
        Permission.TASK_DELETE, Permission.USER_READ, Permission.USER_UPDATE,
    ]),
    Role.VIEWER: frozenset([
        Permission.TASK_READ, Permission.USER_READ,
    ]),
}


def get_permissions(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in get_permissions(role)
