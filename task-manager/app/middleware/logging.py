"""
Middleware untuk logging dan request tracing.

Advanced FastAPI: Custom middleware dengan Starlette.
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk:
    1. Generate unique Request ID setiap request
    2. Log request masuk dan response keluar
    3. Tambahkan header X-Request-ID dan X-Process-Time
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID unik
        request_id = str(uuid.uuid4())[:8]

        # Simpan di request state (bisa diakses dari endpoint)
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "→ %s %s | request_id=%s | client=%s",
            request.method,
            request.url.path,
            request_id,
            request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.error("Request failed | request_id=%s", request_id, exc_info=True)
            raise

        process_time = time.perf_counter() - start_time

        logger.info(
            "← %s %s | status=%d | time=%.3fms | request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            process_time * 1000,
            request_id,
        )

        # Tambahkan custom headers ke response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk inject tenant context dari header X-Tenant-Slug.
    Berguna untuk audit logging dan tenant-aware operations.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_slug = request.headers.get("X-Tenant-Slug")
        request.state.tenant_slug = tenant_slug
        return await call_next(request)
