from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.exception_handlers import app_exception_handler, validation_exception_handler
from app.core.exceptions import AppException
from app.middleware.logging import RequestLoggingMiddleware as LoggingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if not settings.is_production else 0.2,
        profiles_sample_rate=1.0 if not settings.is_production else 0.2,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect Redis
    try:
        from app.infrastructure.cache.redis_client import get_redis
        app.state.redis = get_redis()
        await app.state.redis.ping()
    except Exception:
        app.state.redis = None
    yield
    # Shutdown: close Redis
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(RateLimiterMiddleware, requests_per_minute=60)
app.add_middleware(LoggingMiddleware)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    redis_ok = False
    if app.state.redis:
        try:
            await app.state.redis.ping()
            redis_ok = True
        except Exception:
            pass
    return {"status": "ok", "version": settings.APP_VERSION, "redis": redis_ok}
