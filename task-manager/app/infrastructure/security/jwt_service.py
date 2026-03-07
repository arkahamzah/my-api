import uuid as _uuid
from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


class TokenPayload(BaseModel):
    sub: str
    tenant: str
    role: str
    type: str
    exp: datetime
    iat: datetime
    jti: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class JWTService:
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None,
    ):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm or settings.ALGORITHM
        self.access_expire = timedelta(
            minutes=access_token_expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_expire = timedelta(
            days=refresh_token_expire_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def create_access_token(self, user_id: UUID, tenant_id: str, role: str, jti: str = None) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id), "tenant": tenant_id, "role": role, "type": "access",
            "iat": now, "exp": now + self.access_expire, "jti": jti or str(_uuid.uuid4()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID, tenant_id: str, role: str, jti: str = None) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id), "tenant": tenant_id, "role": role, "type": "refresh",
            "iat": now, "exp": now + self.refresh_expire, "jti": jti or str(_uuid.uuid4()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(self, user_id: UUID, tenant_id: str, role: str) -> TokenPair:
        return TokenPair(
            access_token=self.create_access_token(user_id, tenant_id, role),
            refresh_token=self.create_refresh_token(user_id, tenant_id, role),
            expires_in=int(self.access_expire.total_seconds()),
        )

    def decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload(**payload)
        except JWTError as e:
            raise UnauthorizedError(f"Token tidak valid: {e}")

    def decode_access_token(self, token: str) -> TokenPayload:
        payload = self.decode_token(token)
        if payload.type != "access":
            raise UnauthorizedError("Dibutuhkan access token")
        return payload

    def decode_refresh_token(self, token: str) -> TokenPayload:
        payload = self.decode_token(token)
        if payload.type != "refresh":
            raise UnauthorizedError("Dibutuhkan refresh token")
        return payload
