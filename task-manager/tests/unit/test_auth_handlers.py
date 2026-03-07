from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.application.auth.commands import ChangeRoleCommand, LoginCommand, RegisterUserCommand
from app.application.auth.handlers import ChangeRoleHandler, LoginHandler, RegisterUserHandler
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.domain.entities.user import User
from app.domain.value_objects.role import Role
from app.infrastructure.security.jwt_service import JWTService, TokenPair

TENANT = "t1"

def make_user(role=Role.MEMBER):
    return User.create(email="u@t.com", username="u", hashed_password="h",
                       tenant_id=TENANT, role=role)

class TestRegisterHandler:
    @pytest.fixture
    def setup(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None
        repo.get_by_username.return_value = None
        repo.create.return_value = make_user()
        pwd = MagicMock(); pwd.hash.return_value = "$2b$hash"
        return RegisterUserHandler(user_repo=repo, password_service=pwd), repo, pwd

    async def test_registers(self, setup):
        h, repo, _ = setup
        await h.handle(RegisterUserCommand(email="n@t.com", username="n", password="p12345678", tenant_id=TENANT))
        repo.create.assert_called_once()

    async def test_conflict_email(self, setup):
        h, repo, _ = setup
        repo.get_by_email.return_value = make_user()
        with pytest.raises(ConflictError):
            await h.handle(RegisterUserCommand(email="x@t.com", username="x", password="p12345678", tenant_id=TENANT))

    async def test_conflict_username(self, setup):
        h, repo, _ = setup
        repo.get_by_username.return_value = make_user()
        with pytest.raises(ConflictError):
            await h.handle(RegisterUserCommand(email="y@t.com", username="taken", password="p12345678", tenant_id=TENANT))

    async def test_hashes_password(self, setup):
        h, _, pwd = setup
        await h.handle(RegisterUserCommand(email="n@t.com", username="n", password="plainpass", tenant_id=TENANT))
        pwd.hash.assert_called_once_with("plainpass")

class TestLoginHandler:
    @pytest.fixture
    def setup(self):
        repo = AsyncMock(); repo.get_by_email.return_value = make_user()
        pwd = MagicMock(); pwd.verify.return_value = True
        jwt = MagicMock(spec=JWTService)
        jwt.create_token_pair.return_value = TokenPair(access_token="acc", refresh_token="ref", expires_in=1800)
        return LoginHandler(user_repo=repo, password_service=pwd, jwt_service=jwt), repo, pwd

    async def test_returns_tokens(self, setup):
        h, _, _ = setup
        result = await h.handle(LoginCommand(email="u@t.com", password="pass", tenant_id=TENANT))
        assert result.access_token == "acc"

    async def test_wrong_password(self, setup):
        h, _, pwd = setup; pwd.verify.return_value = False
        with pytest.raises(UnauthorizedError):
            await h.handle(LoginCommand(email="u@t.com", password="wrong", tenant_id=TENANT))

    async def test_unknown_email(self, setup):
        h, repo, _ = setup; repo.get_by_email.return_value = None
        with pytest.raises(UnauthorizedError):
            await h.handle(LoginCommand(email="x@t.com", password="p", tenant_id=TENANT))

    async def test_inactive_user(self, setup):
        h, repo, _ = setup
        u = make_user(); u.deactivate(); repo.get_by_email.return_value = u
        with pytest.raises(ForbiddenError):
            await h.handle(LoginCommand(email="u@t.com", password="p", tenant_id=TENANT))

class TestChangeRoleHandler:
    async def test_admin_can_change_role(self):
        repo = AsyncMock()
        admin = make_user(Role.ADMIN); target = make_user(Role.MEMBER)
        repo.get_by_id.side_effect = [admin, target]; repo.update.return_value = target
        await ChangeRoleHandler(user_repo=repo).handle(
            ChangeRoleCommand(target_user_id=target.id, tenant_id=TENANT,
                              new_role=Role.VIEWER, requested_by=admin.id))
        repo.update.assert_called_once()

    async def test_member_cannot_change_role(self):
        repo = AsyncMock()
        member = make_user(Role.MEMBER); target = make_user(Role.VIEWER)
        repo.get_by_id.side_effect = [member, target]
        with pytest.raises(ForbiddenError):
            await ChangeRoleHandler(user_repo=repo).handle(
                ChangeRoleCommand(target_user_id=target.id, tenant_id=TENANT,
                                  new_role=Role.ADMIN, requested_by=member.id))
