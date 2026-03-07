from uuid import UUID

class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppException):
    def __init__(self, resource: str, id: UUID | str) -> None:
        super().__init__(f"{resource} '{id}' tidak ditemukan", status_code=404)

class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)

class ForbiddenError(AppException):
    def __init__(self, message: str = "Akses ditolak") -> None:
        super().__init__(message, status_code=403)

class UnauthorizedError(AppException):
    def __init__(self, message: str = "Autentikasi diperlukan") -> None:
        super().__init__(message, status_code=401)

class DomainValidationError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)
