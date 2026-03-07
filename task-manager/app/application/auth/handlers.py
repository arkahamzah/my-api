from dataclasses import dataclass
from uuid import UUID

from app.application.auth.commands import (
    ChangePasswordCommand, ChangeRoleCommand, LoginCommand,
    RefreshTokenCommand, RegisterUserCommand, GetUserByIdQuery, ListUsersQuery,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.role import Permission, Role
from app.infrastructure.security.jwt_service import JWTService, TokenPair
from app.infrastructure.security.password_service import PasswordService


@dataclass
class RegisterUserHandler:
    user_repo: UserRepository
    password_service: PasswordService

    async def handle(self, cmd: RegisterUserCommand) -> User:
        if await self.user_repo.get_by_email(cmd.email, cmd.tenant_id):
            raise ConflictError(f"Email '{cmd.email}' sudah terdaftar di tenant ini")
        if await self.user_repo.get_by_username(cmd.username, cmd.tenant_id):
            raise ConflictError(f"Username '{cmd.username}' sudah dipakai")
        hashed = self.password_service.hash(cmd.password)
        user = User.create(email=cmd.email, username=cmd.username, hashed_password=hashed,
                           tenant_id=cmd.tenant_id, role=cmd.role)
        return await self.user_repo.create(user)


@dataclass
class LoginHandler:
    user_repo: UserRepository
    password_service: PasswordService
    jwt_service: JWTService

    async def handle(self, cmd: LoginCommand) -> TokenPair:
        user = await self.user_repo.get_by_email(cmd.email, cmd.tenant_id)
        if not user:
            raise UnauthorizedError("Email atau password salah")
        if not user.is_active:
            raise ForbiddenError("Akun telah dinonaktifkan")
        if not self.password_service.verify(cmd.password, user.hashed_password):
            raise UnauthorizedError("Email atau password salah")
        return self.jwt_service.create_token_pair(user.id, user.tenant_id, user.role.value)


@dataclass
class RefreshTokenHandler:
    user_repo: UserRepository
    jwt_service: JWTService

    async def handle(self, cmd: RefreshTokenCommand) -> TokenPair:
        payload = self.jwt_service.decode_refresh_token(cmd.refresh_token)
        user = await self.user_repo.get_by_id(UUID(payload.sub), payload.tenant)
        if not user:
            raise UnauthorizedError("User tidak ditemukan")
        if not user.is_active:
            raise ForbiddenError("Akun telah dinonaktifkan")
        return self.jwt_service.create_token_pair(user.id, user.tenant_id, user.role.value)


@dataclass
class ChangePasswordHandler:
    user_repo: UserRepository
    password_service: PasswordService

    async def handle(self, cmd: ChangePasswordCommand) -> None:
        user = await self.user_repo.get_by_id(cmd.user_id, cmd.tenant_id)
        if not user:
            raise NotFoundError("User", cmd.user_id)
        if not self.password_service.verify(cmd.current_password, user.hashed_password):
            raise UnauthorizedError("Password saat ini salah")
        user.hashed_password = self.password_service.hash(cmd.new_password)
        await self.user_repo.update(user)


@dataclass
class ChangeRoleHandler:
    user_repo: UserRepository

    async def handle(self, cmd: ChangeRoleCommand) -> User:
        requester = await self.user_repo.get_by_id(cmd.requested_by, cmd.tenant_id)
        if not requester:
            raise NotFoundError("User", cmd.requested_by)
        if not requester.has_permission(Permission.USER_UPDATE_ALL):
            raise ForbiddenError("Hanya admin yang bisa mengubah role")
        target = await self.user_repo.get_by_id(cmd.target_user_id, cmd.tenant_id)
        if not target:
            raise NotFoundError("User", cmd.target_user_id)
        if requester.id == target.id and cmd.new_role != Role.ADMIN:
            raise ForbiddenError("Tidak bisa menurunkan role diri sendiri")
        target.change_role(cmd.new_role)
        return await self.user_repo.update(target)


@dataclass
class GetUserByIdHandler:
    user_repo: UserRepository

    async def handle(self, query: GetUserByIdQuery) -> User:
        user = await self.user_repo.get_by_id(query.user_id, query.tenant_id)
        if not user:
            raise NotFoundError("User", query.user_id)
        return user


@dataclass
class ListUsersHandler:
    user_repo: UserRepository

    async def handle(self, query: ListUsersQuery) -> list[User]:
        return await self.user_repo.list_by_tenant(
            tenant_id=query.tenant_id, limit=query.limit, offset=query.offset)
