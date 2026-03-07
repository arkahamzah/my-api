from uuid import uuid4
import pytest
from app.core.exceptions import UnauthorizedError
from app.infrastructure.security.jwt_service import JWTService

SECRET = "test-secret-key-for-unit-tests-minimum-32-chars!!"
TENANT = "tenant-abc"

@pytest.fixture
def svc():
    return JWTService(secret_key=SECRET, access_token_expire_minutes=30, refresh_token_expire_days=7)

@pytest.fixture
def uid():
    return uuid4()

class TestAccessToken:
    def test_creates_valid_token(self, svc, uid):
        assert len(svc.create_access_token(uid, TENANT, "member")) > 0

    def test_payload_fields(self, svc, uid):
        p = svc.decode_access_token(svc.create_access_token(uid, TENANT, "admin"))
        assert p.sub == str(uid) and p.tenant == TENANT and p.role == "admin" and p.type == "access"

    def test_has_jti(self, svc, uid):
        assert svc.decode_access_token(svc.create_access_token(uid, TENANT, "member")).jti

class TestRefreshToken:
    def test_type_is_refresh(self, svc, uid):
        assert svc.decode_refresh_token(svc.create_refresh_token(uid, TENANT, "member")).type == "refresh"

    def test_access_raises_on_refresh(self, svc, uid):
        with pytest.raises(UnauthorizedError):
            svc.decode_access_token(svc.create_refresh_token(uid, TENANT, "member"))

    def test_refresh_raises_on_access(self, svc, uid):
        with pytest.raises(UnauthorizedError):
            svc.decode_refresh_token(svc.create_access_token(uid, TENANT, "member"))

class TestTokenPair:
    def test_pair_fields(self, svc, uid):
        pair = svc.create_token_pair(uid, TENANT, "member")
        assert pair.access_token and pair.refresh_token and pair.token_type == "bearer"

    def test_tokens_differ(self, svc, uid):
        pair = svc.create_token_pair(uid, TENANT, "member")
        assert pair.access_token != pair.refresh_token

class TestInvalidTokens:
    def test_garbage_raises(self, svc):
        with pytest.raises(UnauthorizedError):
            svc.decode_token("not.a.token")

    def test_tampered_raises(self, svc, uid):
        token = svc.create_access_token(uid, TENANT, "member")
        with pytest.raises(UnauthorizedError):
            svc.decode_access_token(token[:-5] + "XXXXX")

    def test_wrong_secret_raises(self, uid):
        a = JWTService(secret_key="secret-A-minimum-32-chars-paddingg")
        b = JWTService(secret_key="secret-B-minimum-32-chars-paddingg")
        with pytest.raises(UnauthorizedError):
            b.decode_access_token(a.create_access_token(uid, TENANT, "member"))

    def test_expired_raises(self, uid):
        svc = JWTService(secret_key=SECRET, access_token_expire_minutes=-1)
        with pytest.raises(UnauthorizedError):
            svc.decode_access_token(svc.create_access_token(uid, TENANT, "member"))
