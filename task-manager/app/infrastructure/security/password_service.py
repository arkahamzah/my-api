from passlib.context import CryptContext


class PasswordService:
    def __init__(self, rounds: int = 12):
        self._context = CryptContext(
            schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=rounds
        )

    def hash(self, plain_password: str) -> str:
        return self._context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)

    def needs_rehash(self, hashed_password: str) -> bool:
        return self._context.needs_update(hashed_password)
