from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from redis import Redis
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.entities import HoneypotNode


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
    try:
        client = Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        heartbeat = client.get("honeypot:worker:heartbeat")
        client.close()
        return {"status": "healthy" if heartbeat else "unhealthy", "heartbeat": heartbeat}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__}


@router.get("/honeypots")
def honeypot_health() -> dict:
    try:
        with SessionLocal() as db:
            rows = db.scalars(select(HoneypotNode).where(HoneypotNode.enabled.is_(True))).all()
        cutoff = datetime.now(UTC) - timedelta(seconds=30)
        nodes = [
            {
                "name": row.name,
                "kind": row.kind,
                "last_seen_at": row.last_seen_at,
                "status": "healthy" if row.last_seen_at and (row.last_seen_at.replace(tzinfo=UTC) if row.last_seen_at.tzinfo is None else row.last_seen_at) >= cutoff else "unhealthy",
            }
            for row in rows
        ]
        return {"status": "healthy" if nodes and all(row["status"] == "healthy" for row in nodes) else "unhealthy", "nodes": nodes}
    except Exception as exc:
        return {"status": "unhealthy", "error": type(exc).__name__, "nodes": []}
