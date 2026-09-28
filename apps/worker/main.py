import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from redis import Redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Alert, Attacker, Event, Incident, IncidentEvent, MLPrediction, Notification, ThreatIntel
from ml.features import extract_from_events
from ml.predict import predict


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
    with Session(engine) as db:
        cached = db.scalar(select(ThreatIntel).where(ThreatIntel.source_ip == source_ip, ThreatIntel.provider == "configured"))
        if cached and cached.expires_at and cached.expires_at > datetime.now(UTC):
            return
    status = "UNAVAILABLE"
    data: dict = {}
    if provider_url and api_key:
        for attempt in range(3):
            try:
                response = httpx.get(
                    provider_url.rstrip("/") + "/" + source_ip,
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=float(os.getenv("THREAT_INTEL_TIMEOUT_SECONDS", "3")),
                )
                response.raise_for_status()
                data = response.json()
                status = "AVAILABLE"
                break
            except (httpx.HTTPError, ValueError) as exc:
                status = "ERROR"
                data = {"error": type(exc).__name__}
                if attempt < 2:
                    time.sleep(0.25 * (2**attempt))
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


def classify_incident(event_id: str) -> None:
    model_path = Path(os.getenv("ML_MODEL_PATH", "/app/ml/model/baseline.joblib"))
    if not model_path.is_file():
        return
    with Session(engine) as db:
        incident = db.scalar(select(Incident).join(IncidentEvent).where(IncidentEvent.event_id == event_id))
        if incident is None:
            return
        events = db.scalars(
            select(Event)
            .options(selectinload(Event.detections))
            .join(IncidentEvent, IncidentEvent.event_id == Event.id)
            .where(IncidentEvent.incident_id == incident.id)
        ).unique().all()
        features = extract_from_events(events)
        result = predict(model_path, features)
        record = db.scalar(
            select(MLPrediction).where(
                MLPrediction.incident_id == incident.id,
                MLPrediction.model_version == result["model_version"],
            )
        )
        if record is None:
            record = MLPrediction(incident_id=incident.id, model_version=str(result["model_version"]))
            db.add(record)
        record.classification = str(result["classification"])
        record.confidence = float(result["confidence"])
        record.features = features
        db.commit()


def deliver_alert(event_id: str) -> None:
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    with Session(engine) as db:
        alert = db.scalar(select(Alert).join(IncidentEvent, IncidentEvent.incident_id == Alert.incident_id).where(IncidentEvent.event_id == event_id))
        if alert is None:
            return
        notification = db.scalar(select(Notification).where(Notification.alert_id == alert.id, Notification.channel == "IN_APP"))
        if notification is None:
            notification = Notification(alert_id=alert.id, channel="IN_APP", status="DELIVERED", delivered_at=datetime.now(UTC))
            db.add(notification)
        if webhook_url:
            webhook = db.scalar(select(Notification).where(Notification.alert_id == alert.id, Notification.channel == "WEBHOOK"))
            if webhook is None or webhook.status == "FAILED":
                if webhook is None:
                    webhook = Notification(alert_id=alert.id, channel="WEBHOOK", status="PENDING")
                    db.add(webhook)
                    db.flush()
                else:
                    webhook.status = "PENDING"
                try:
                    response = httpx.post(
                        webhook_url,
                        json={"alert_id": alert.id, "incident_id": alert.incident_id, "title": alert.title, "severity": alert.severity.value},
                        timeout=3.0,
                    )
                    response.raise_for_status()
                    webhook.status = "DELIVERED"
                    webhook.delivered_at = datetime.now(UTC)
                except httpx.HTTPError:
                    webhook.status = "FAILED"
        db.commit()


def run() -> None:
    try:
        redis.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise
    logger.info(json.dumps({"timestamp": datetime.now(UTC).isoformat(), "service": "worker", "event": "started"}))
    while True:
        redis.set("honeypot:worker:heartbeat", datetime.now(UTC).isoformat(), ex=15)
        batches = redis.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=20, block=5000)
        for _, messages in batches:
            for message_id, fields in messages:
                try:
                    if fields.get("kind") == "enrich_event":
                        enrich_ip(fields["source_ip"])
                        classify_incident(fields["event_id"])
                        deliver_alert(fields["event_id"])
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
