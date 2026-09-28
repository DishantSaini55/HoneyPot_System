import html
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from honeypot_sensor import EventClient, EventEnvelope


PORT = int(os.getenv("HTTP_HONEYPOT_PORT", "8080"))
MAX_CAPTURE_BYTES = int(os.getenv("HTTP_MAX_CAPTURE_BYTES", "65536"))
SESSION_COOKIE = "HPSESSION"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("http-honeypot")
event_client: EventClient | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global event_client
    event_client = EventClient()
    try:
        yield
    finally:
        if event_client:
            await event_client.close()


app = FastAPI(title="Decoy HTTP Service", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    return {"status": "healthy"}


def decoy_response(path: str, method: str) -> Response:
    normalized = path.lower().rstrip("/") or "/"
    if normalized in {"/login", "/admin", "/wp-login.php", "/phpmyadmin"}:
        title = "Administrator Sign In"
        body = (
            "<!doctype html><html><head><title>" + title + "</title></head><body>"
            "<h1>" + title + "</h1><form method='post'>"
            "<label>Username <input name='username' autocomplete='off'></label>"
            "<label>Password <input type='password' name='password' autocomplete='off'></label>"
            "<button type='submit'>Sign in</button></form>"
            + ("<p>Invalid username or password.</p>" if method == "POST" else "")
            + "</body></html>"
        )
        return HTMLResponse(body, status_code=401 if method == "POST" else 200)
    if normalized == "/robots.txt":
        return PlainTextResponse("User-agent: *\nDisallow: /admin\nDisallow: /backup\n")
    if normalized in {"/.env", "/config", "/config.json"}:
        return PlainTextResponse("Not Found", status_code=404)
    if normalized.startswith("/api"):
        return JSONResponse({"error": "authentication required"}, status_code=401)
    if normalized == "/":
        return HTMLResponse("<!doctype html><title>Acme Portal</title><h1>Service Portal</h1>")
    safe_path = html.escape(path[:256])
    return HTMLResponse(f"<!doctype html><title>404</title><h1>Not Found</h1><p>{safe_path}</p>", status_code=404)


def filtered_headers(request: Request) -> dict[str, str]:
    redacted = {"authorization", "cookie", "proxy-authorization"}
    return {
        key.lower(): ("[REDACTED]" if key.lower() in redacted else value[:2048])
        for key, value in request.headers.items()
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def capture(request: Request, path: str) -> Response:
    raw_body = await request.body()
    captured = raw_body[:MAX_CAPTURE_BYTES]
    response = decoy_response(request.url.path, request.method)
    session_id = request.cookies.get(SESSION_COOKIE) or str(uuid.uuid4())
    source_ip = request.client.host if request.client else "0.0.0.0"
    source_port = request.client.port if request.client else None
    payload = {
        "node_name": os.getenv("HONEYPOT_NODE_NAME", "http-primary"),
        "method": request.method,
        "path": request.url.path,
        "raw_target": request.scope.get("raw_path", b"").decode("latin-1", errors="replace")
        + (f"?{request.url.query}" if request.url.query else ""),
        "query": dict(request.query_params.multi_items()),
        "query_string": request.url.query,
        "headers": filtered_headers(request),
        "referer": request.headers.get("referer"),
        "body_size": len(raw_body),
        "body_truncated": len(raw_body) > len(captured),
        "body_preview": captured.decode("utf-8", errors="replace"),
        "response_code": response.status_code,
    }
    event = EventEnvelope(
        source_ip=source_ip,
        source_port=source_port,
        destination_port=PORT,
        protocol="HTTP",
        honeypot="HTTP",
        session_id=session_id,
        event_type="HTTP_REQUEST",
        user_agent=request.headers.get("user-agent"),
        payload=payload,
    )
    accepted = await event_client.send(event) if event_client else False
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "service": "http-honeypot",
                "event": "request_captured",
                "event_id": event.event_id,
                "session_id": session_id,
                "source_ip": source_ip,
                "method": request.method,
                "path": request.url.path,
                "ingested": accepted,
            }
        )
    )
    if SESSION_COOKIE not in request.cookies:
        response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="strict", secure=False, max_age=1800)
    return response
