import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis

from app.api import auth, health, ingestion, management
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level, "api")
local_ingestion_requests: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(
    title="HoneyPot System API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_security(request: Request, call_next):
    if request.url.path == "/api/v1/ingest/events":
        content_length = request.headers.get("content-length")
        try:
            oversized = bool(content_length) and int(content_length) > settings.max_event_body_bytes
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
        if oversized:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
        source = request.client.host if request.client else "unknown"
        minute = int(time.time() // 60)
        limited = False
        try:
            client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.1, socket_timeout=0.1)
            key = f"honeypot:rate:ingest:{source}:{minute}"
            count = client.incr(key)
            if count == 1:
                client.expire(key, 65)
            client.close()
            limited = count > settings.ingestion_rate_limit_per_minute
        except Exception:
            now = time.monotonic()
            queue = local_ingestion_requests[source]
            while queue and queue[0] < now - 60:
                queue.popleft()
            queue.append(now)
            limited = len(queue) > settings.ingestion_rate_limit_per_minute
        if limited:
            return JSONResponse({"detail": "Ingestion rate limit exceeded"}, status_code=429)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(management.router, prefix="/api/v1")
