from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionLocal


router = APIRouter(prefix="/health", tags=["health"])


def _database_status() -> dict:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__}


def _redis_status() -> dict:
    try:
        client = Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        client.ping()
        client.close()
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__}


@router.get("")
def health() -> dict:
    return {"status": "healthy", "service": "api"}


@router.get("/database")
def database_health() -> dict:
    return _database_status()


@router.get("/redis")
def redis_health() -> dict:
    return _redis_status()


@router.get("/workers")
def worker_health() -> dict:
    status = _redis_status()
    return {"status": status["status"], "detail": "Worker queue uses Redis Streams", **({"error": status["error"]} if "error" in status else {})}


@router.get("/honeypots")
def honeypot_health() -> dict:
    try:
        with SessionLocal() as db:
            rows = db.execute(text("SELECT name, kind, last_seen_at FROM honeypot_nodes WHERE enabled = true")).mappings().all()
        return {"status": "healthy", "nodes": [dict(row) for row in rows]}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__, "nodes": []}

