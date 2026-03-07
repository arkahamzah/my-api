"""
Rate limiting middleware - per IP, sliding window via Redis.
Graceful degradation: jika Redis down, request tetap lolos.
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.rpm = requests_per_minute
        self.window = 60

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip untuk health check
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"

        try:
            redis = request.app.state.redis
            now = int(time.time())
            window_start = now - self.window

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window)
            results = await pipe.execute()

            count = results[2]
            if count > self.rpm:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Terlalu banyak request. Coba lagi sebentar."},
                    headers={"Retry-After": "60"},
                )
        except Exception as e:
            logger.warning("Rate limiter Redis error: %s — skipping limit", e)

        return await call_next(request)
