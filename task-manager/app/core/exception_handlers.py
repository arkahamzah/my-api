from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": type(exc).__name__},
    )


def _sanitize_errors(errors: list) -> list:
    """Pastikan semua nilai di errors bisa di-JSON-serialize."""
    sanitized = []
    for err in errors:
        clean = {}
        for k, v in err.items():
            if k == "ctx":
                # ctx bisa berisi Exception object → ubah ke string
                clean[k] = {ck: str(cv) for ck, cv in v.items()}
            else:
                clean[k] = v
        sanitized.append(clean)
    return sanitized


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Validasi gagal", "errors": _sanitize_errors(exc.errors())},
    )
