import json
import logging
import os
from datetime import UTC, datetime, timedelta

import httpx
from redis import Redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.entities import Attacker, ThreatIntel


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("worker")
redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
STREAM = "honeypot:jobs"
GROUP = "workers"
CONSUMER = os.getenv("WORKER_NAME", "worker-1")


def enrich_ip(source_ip: str) -> None:
    provider_url = os.getenv("THREAT_INTEL_PROVIDER_URL")
    api_key = os.getenv("THREAT_INTEL_API_KEY")
    status = "UNAVAILABLE"
    data: dict = {}
    if provider_url and api_key:
        try:
            response = httpx.get(
                provider_url.rstrip("/") + "/" + source_ip,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=float(os.getenv("THREAT_INTEL_TIMEOUT_SECONDS", "3")),
            )
            response.raise_for_status()
            data = response.json()
            status = "AVAILABLE"
        except (httpx.HTTPError, ValueError) as exc:
            status = "ERROR"
            data = {"error": type(exc).__name__}
    with Session(engine) as db:
        record = db.scalar(select(ThreatIntel).where(ThreatIntel.source_ip == source_ip, ThreatIntel.provider == "configured"))
        if record is None:
            record = ThreatIntel(source_ip=source_ip, provider="configured")
            db.add(record)
        record.status = status
        record.data = data
        record.checked_at = datetime.now(UTC)
        record.expires_at = datetime.now(UTC) + timedelta(hours=24)
        attacker = db.scalar(select(Attacker).where(Attacker.source_ip == source_ip))
        if attacker and status == "AVAILABLE":
            attacker.country = data.get("country_code")
            attacker.city = data.get("city")
            attacker.latitude = data.get("latitude")
            attacker.longitude = data.get("longitude")
            attacker.asn = str(data["asn"]) if data.get("asn") is not None else None
            attacker.organization = data.get("organization")
        db.commit()


def run() -> None:
    try:
        redis.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise
    logger.info(json.dumps({"timestamp": datetime.now(UTC).isoformat(), "service": "worker", "event": "started"}))
    while True:
        batches = redis.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=20, block=5000)
        for _, messages in batches:
            for message_id, fields in messages:
                try:
                    if fields.get("kind") == "enrich_event":
                        enrich_ip(fields["source_ip"])
                    redis.xack(STREAM, GROUP, message_id)
                except Exception as exc:
                    logger.error(
                        json.dumps(
                            {
                                "timestamp": datetime.now(UTC).isoformat(),
                                "service": "worker",
                                "event": "job_failed",
                                "message_id": message_id,
                                "error": type(exc).__name__,
                            }
                        )
                    )


if __name__ == "__main__":
    run()

