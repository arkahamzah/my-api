from typing import Annotated
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.services.cache_service import CacheService, NullCacheService
from app.application.use_cases.task_use_cases import TaskUseCases
from app.application.use_cases.tenant_use_cases import TenantUseCases
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository
from app.infrastructure.repositories.tenant_repository import SQLAlchemyTenantRepository

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_cache(request: Request) -> CacheService:
    try:
        from app.infrastructure.cache.redis_cache import RedisCacheService
        return RedisCacheService(request.app.state.redis)
    except Exception:
        return NullCacheService()


CacheDep = Annotated[CacheService, Depends(get_cache)]


def get_task_use_cases(session: SessionDep, cache: CacheDep) -> TaskUseCases:
    return TaskUseCases(SQLAlchemyTaskRepository(session), cache)


def get_tenant_use_cases(session: SessionDep, cache: CacheDep) -> TenantUseCases:
    return TenantUseCases(SQLAlchemyTenantRepository(session), cache)


TaskUseCasesDep = Annotated[TaskUseCases, Depends(get_task_use_cases)]
TenantUseCasesDep = Annotated[TenantUseCases, Depends(get_tenant_use_cases)]


# ── Phase 4: Auth Dependencies ────────────────────────────────────────────────
from uuid import UUID as _UUID

from fastapi import Header as _Header, HTTPException as _HTTPException, status as _status
from fastapi.security import HTTPAuthorizationCredentials as _HTTPAuthCreds, HTTPBearer as _HTTPBearer

from app.application.auth.handlers import (
    ChangePasswordHandler, ChangeRoleHandler, ListUsersHandler,
    LoginHandler, RefreshTokenHandler, RegisterUserHandler,
)
from app.core.exceptions import ForbiddenError as _ForbiddenError, UnauthorizedError as _UnauthorizedError
from app.domain.entities.user import User
from app.domain.value_objects.role import Permission
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_service import PasswordService

_bearer_scheme = _HTTPBearer(auto_error=False)
_jwt_service = JWTService()
_password_service = PasswordService()


def get_jwt_service() -> JWTService:
    return _jwt_service


def get_password_service() -> PasswordService:
    return _password_service


def get_user_repository(session: SessionDep) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


UserRepoDep = Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)]


def get_register_handler(
    user_repo: UserRepoDep,
    pwd: Annotated[PasswordService, Depends(get_password_service)],
) -> RegisterUserHandler:
    return RegisterUserHandler(user_repo=user_repo, password_service=pwd)


def get_login_handler(
    user_repo: UserRepoDep,
    pwd: Annotated[PasswordService, Depends(get_password_service)],
    jwt: Annotated[JWTService, Depends(get_jwt_service)],
) -> LoginHandler:
    return LoginHandler(user_repo=user_repo, password_service=pwd, jwt_service=jwt)


def get_refresh_handler(
    user_repo: UserRepoDep,
    jwt: Annotated[JWTService, Depends(get_jwt_service)],
) -> RefreshTokenHandler:
    return RefreshTokenHandler(user_repo=user_repo, jwt_service=jwt)


def get_change_password_handler(
    user_repo: UserRepoDep,
    pwd: Annotated[PasswordService, Depends(get_password_service)],
) -> ChangePasswordHandler:
    return ChangePasswordHandler(user_repo=user_repo, password_service=pwd)


def get_change_role_handler(user_repo: UserRepoDep) -> ChangeRoleHandler:
    return ChangeRoleHandler(user_repo=user_repo)


def get_list_users_handler(user_repo: UserRepoDep) -> ListUsersHandler:
    return ListUsersHandler(user_repo=user_repo)


async def get_current_user(
    credentials: Annotated[_HTTPAuthCreds | None, Depends(_bearer_scheme)],
    user_repo: UserRepoDep,
    jwt: Annotated[JWTService, Depends(get_jwt_service)],
    x_tenant_id: Annotated[str | None, _Header(alias="X-Tenant-ID")] = None,
) -> User:
    if credentials is None:
        raise _HTTPException(
            status_code=_status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not x_tenant_id:
        raise _HTTPException(
            status_code=_status.HTTP_401_UNAUTHORIZED,
            detail="Header X-Tenant-ID diperlukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode_access_token(credentials.credentials)
    except _UnauthorizedError as e:
        raise _HTTPException(
            status_code=_status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.tenant != x_tenant_id:
        raise _HTTPException(
            status_code=_status.HTTP_403_FORBIDDEN,
            detail="Token tidak sesuai dengan tenant ini",
        )
    user = await user_repo.get_by_id(_UUID(payload.sub), x_tenant_id)
    if not user:
        raise _HTTPException(status_code=_status.HTTP_401_UNAUTHORIZED, detail="User tidak ditemukan")
    if not user.is_active:
        raise _HTTPException(status_code=_status.HTTP_403_FORBIDDEN, detail="Akun dinonaktifkan")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_permission(permission: Permission):
    async def _check(current_user: CurrentUserDep) -> User:
        if not current_user.has_permission(permission):
            raise _HTTPException(
                status_code=_status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak: butuh permission '{permission.value}'",
            )
        return current_user
    return Depends(_check)
