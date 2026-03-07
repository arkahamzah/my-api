from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from app.application.auth.commands import (
    ChangePasswordCommand, ChangeRoleCommand, ListUsersQuery,
    LoginCommand, RefreshTokenCommand, RegisterUserCommand,
)
from app.application.auth.handlers import (
    ChangePasswordHandler, ChangeRoleHandler, ListUsersHandler,
    LoginHandler, RefreshTokenHandler, RegisterUserHandler,
)
from app.core.dependencies import (
    CurrentUserDep, require_permission,
    get_change_password_handler, get_change_role_handler, get_list_users_handler,
    get_login_handler, get_refresh_handler, get_register_handler,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.domain.value_objects.role import Permission, Role

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Username minimal 3 karakter")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool
    tenant_id: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password baru minimal 8 karakter")
        return v


class ChangeRoleRequest(BaseModel):
    user_id: UUID
    new_role: Role


def _user_resp(user) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, username=user.username,
                        role=user.role.value, is_active=user.is_active, tenant_id=user.tenant_id)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    handler: Annotated[RegisterUserHandler, Depends(get_register_handler)],
):
    try:
        user = await handler.handle(RegisterUserCommand(
            email=body.email, username=body.username,
            password=body.password, tenant_id=x_tenant_id))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    return _user_resp(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    handler: Annotated[LoginHandler, Depends(get_login_handler)],
):
    try:
        tokens = await handler.handle(LoginCommand(
            email=body.email, password=body.password, tenant_id=x_tenant_id))
    except (UnauthorizedError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token,
                         token_type=tokens.token_type, expires_in=tokens.expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    handler: Annotated[RefreshTokenHandler, Depends(get_refresh_handler)],
):
    try:
        tokens = await handler.handle(RefreshTokenCommand(refresh_token=body.refresh_token))
    except (UnauthorizedError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token,
                         token_type=tokens.token_type, expires_in=tokens.expires_in)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUserDep):
    return _user_resp(current_user)


@router.put("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUserDep,
    handler: Annotated[ChangePasswordHandler, Depends(get_change_password_handler)],
):
    try:
        await handler.handle(ChangePasswordCommand(
            user_id=current_user.id, tenant_id=current_user.tenant_id,
            current_password=body.current_password, new_password=body.new_password))
    except UnauthorizedError as e:
        raise HTTPException(status_code=401, detail=e.message)


@router.put("/users/role", response_model=UserResponse)
async def change_role(
    body: ChangeRoleRequest,
    current_user: CurrentUserDep,
    _: Annotated[None, require_permission(Permission.ADMIN_PANEL)],
    handler: Annotated[ChangeRoleHandler, Depends(get_change_role_handler)],
):
    try:
        user = await handler.handle(ChangeRoleCommand(
            target_user_id=body.user_id, tenant_id=current_user.tenant_id,
            new_role=body.new_role, requested_by=current_user.id))
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return _user_resp(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: CurrentUserDep,
    _: Annotated[None, require_permission(Permission.USER_READ_ALL)],
    handler: Annotated[ListUsersHandler, Depends(get_list_users_handler)],
    limit: int = 20,
    offset: int = 0,
):
    users = await handler.handle(
        ListUsersQuery(tenant_id=current_user.tenant_id, limit=limit, offset=offset))
    return [_user_resp(u) for u in users]
