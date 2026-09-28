import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession, selectinload

from app.core.config import get_settings
from app.detectors.rules import DetectionContext, analyze_event, calculate_risk_score, severity_for_score
from app.models.entities import (
    Alert,
    AlertStatus,
    Attacker,
    CommandEvent,
    CredentialCapture,
    Detection,
    Event,
    HoneypotNode,
    HttpRequest,
    Incident,
    IncidentEvent,
    IncidentStatus,
    Session,
    SessionStatus,
    Severity,
)
from app.schemas.events import EventCreate


@dataclass
class IngestionResult:
    event: Event
    incident: Incident | None
    alert: Alert | None
    duplicate: bool = False


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def ingest_event(db: DBSession, incoming: EventCreate) -> IngestionResult:
    duplicate = db.scalar(
        select(Event).options(selectinload(Event.detections)).where(Event.id == incoming.event_id)
    )
    if duplicate:
        incident = db.scalar(
            select(Incident)
            .join(IncidentEvent, IncidentEvent.incident_id == Incident.id)
            .where(IncidentEvent.event_id == duplicate.id)
        )
        alert = db.scalar(select(Alert).where(Alert.incident_id == incident.id)) if incident else None
        return IngestionResult(duplicate, incident, alert, duplicate=True)

    source_ip = str(incoming.source_ip)
    node = _get_or_create_node(db, incoming)
    attacker = _get_or_create_attacker(db, source_ip, incoming.timestamp)
    session = _get_or_create_session(db, incoming, attacker, node)
    context = _build_context(db, incoming, source_ip)
    matches = analyze_event(incoming, context)
    score = calculate_risk_score(matches)
    severity = Severity(severity_for_score(score))

    event = Event(
        id=incoming.event_id,
        timestamp=incoming.timestamp,
        source_ip=source_ip,
        source_port=incoming.source_port,
        destination_port=incoming.destination_port,
        protocol=incoming.protocol,
        honeypot=incoming.honeypot,
        session_id=incoming.session_id,
        event_type=incoming.event_type,
        username=incoming.username,
        command=incoming.command,
        user_agent=incoming.user_agent,
        payload=incoming.payload,
        severity=severity,
        risk_score=score,
    )
    db.add(event)
    db.flush()

    for match in matches:
        db.add(
            Detection(
                event_id=event.id,
                rule_id=match.rule_id,
                attack_type=match.attack_type,
                score=match.score,
                evidence=match.evidence,
            )
        )

    _add_specialized_record(db, event, incoming)
    incident = _correlate_incident(db, event, matches)
    alert = _create_alert_if_required(db, incident) if incident else None

    if incoming.event_type in {"SESSION_ENDED", "DISCONNECTED"}:
        session.status = SessionStatus.CLOSED
        session.ended_at = incoming.timestamp

    db.commit()
    db.refresh(event)
    event = db.scalar(select(Event).options(selectinload(Event.detections)).where(Event.id == event.id))
    assert event is not None
    _enqueue_background_work(event.id, source_ip)
    return IngestionResult(event, incident, alert)


def _get_or_create_node(db: DBSession, incoming: EventCreate) -> HoneypotNode:
    name = str(incoming.payload.get("node_name") or f"{incoming.honeypot.lower()}-{incoming.destination_port}")
    node = db.scalar(select(HoneypotNode).where(HoneypotNode.name == name))
    if node is None:
        node = HoneypotNode(name=name, kind=incoming.honeypot, listen_port=incoming.destination_port)
        db.add(node)
        db.flush()
    node.last_seen_at = incoming.timestamp
    return node


def _get_or_create_attacker(db: DBSession, source_ip: str, timestamp: datetime) -> Attacker:
    attacker = db.scalar(select(Attacker).where(Attacker.source_ip == source_ip))
    if attacker is None:
        attacker = Attacker(source_ip=source_ip, first_seen_at=timestamp, last_seen_at=timestamp)
        db.add(attacker)
        db.flush()
    else:
        attacker.last_seen_at = max(_as_utc(attacker.last_seen_at), _as_utc(timestamp))
    return attacker


def _get_or_create_session(
    db: DBSession,
    incoming: EventCreate,
    attacker: Attacker,
    node: HoneypotNode,
) -> Session:
    session = db.get(Session, incoming.session_id)
    if session is None:
        session = Session(
            id=incoming.session_id,
            attacker_id=attacker.id,
            node_id=node.id,
            protocol=incoming.protocol,
            source_port=incoming.source_port,
            destination_port=incoming.destination_port,
            started_at=incoming.timestamp,
        )
        db.add(session)
        db.flush()
    return session


def _build_context(db: DBSession, incoming: EventCreate, source_ip: str) -> DetectionContext:
    since = incoming.timestamp - timedelta(seconds=60)
    recent_base = (Event.source_ip == source_ip, Event.timestamp >= since, Event.timestamp <= incoming.timestamp)
    auth_count = db.scalar(
        select(func.count(Event.id)).where(
            *recent_base, Event.event_type.in_(["LOGIN_ATTEMPT", "LOGIN_FAILURE", "AUTH_FAILURE"])
        )
    ) or 0
    request_count = db.scalar(
        select(func.count(Event.id)).where(*recent_base, Event.protocol == "HTTP")
    ) or 0
    sensitive_count = db.scalar(
        select(func.count(Event.id)).where(
            *recent_base,
            Event.protocol == "HTTP",
            Event.payload["path"].as_string().in_(["/admin", "/wp-login.php", "/phpmyadmin", "/.env", "/config"]),
        )
    ) or 0
    return DetectionContext(
        recent_auth_failures=int(auth_count)
        + (1 if incoming.event_type in {"LOGIN_ATTEMPT", "LOGIN_FAILURE", "AUTH_FAILURE"} else 0),
        recent_request_count=int(request_count) + (1 if incoming.protocol == "HTTP" else 0),
        recent_sensitive_paths=int(sensitive_count)
        + (1 if str(incoming.payload.get("path", "")).lower() in {"/admin", "/wp-login.php", "/phpmyadmin", "/.env", "/config"} else 0),
    )


def _add_specialized_record(db: DBSession, event: Event, incoming: EventCreate) -> None:
    if incoming.password is not None and incoming.username is not None:
        secret = get_settings().jwt_secret.get_secret_value().encode("utf-8")
        fingerprint = hmac.new(secret, incoming.password.encode("utf-8"), hashlib.sha256).hexdigest()
        db.add(
            CredentialCapture(
                event_id=event.id,
                username=incoming.username,
                password_ciphertext=None,
                password_fingerprint=fingerprint,
            )
        )
    if incoming.command is not None:
        db.add(
            CommandEvent(
                event_id=event.id,
                command=incoming.command,
                simulated_response=incoming.simulated_response,
            )
        )
    if incoming.protocol == "HTTP":
        payload = incoming.payload
        db.add(
            HttpRequest(
                event_id=event.id,
                method=str(payload.get("method", "GET"))[:16],
                path=str(payload.get("path", "/")),
                query=dict(payload.get("query", {})),
                headers=dict(payload.get("headers", {})),
                referer=payload.get("referer"),
                body_size=int(payload.get("body_size", 0)),
                response_code=int(payload.get("response_code", 200)),
            )
        )


def _correlate_incident(db: DBSession, event: Event, matches: list) -> Incident | None:
    if not matches:
        return None
    window_start = event.timestamp - timedelta(minutes=15)
    incident = db.scalar(
        select(Incident)
        .where(
            Incident.source_ip == event.source_ip,
            Incident.status != IncidentStatus.RESOLVED,
            Incident.last_seen_at >= window_start,
        )
        .order_by(Incident.last_seen_at.desc())
    )
    types = sorted({match.attack_type for match in matches})
    if incident is None:
        next_number = (db.scalar(select(func.max(Incident.incident_number))) or 0) + 1
        incident = Incident(
            incident_number=next_number,
            source_ip=event.source_ip,
            attack_type=" + ".join(types),
            severity=event.severity,
            risk_score=event.risk_score,
            first_seen_at=event.timestamp,
            last_seen_at=event.timestamp,
        )
        db.add(incident)
        db.flush()
    else:
        existing_types = set(incident.attack_type.split(" + "))
        incident.attack_type = " + ".join(sorted(existing_types | set(types)))
        incident.risk_score = min(100, max(incident.risk_score, event.risk_score) + min(10, len(matches) * 2))
        incident.severity = Severity(severity_for_score(incident.risk_score))
        incident.last_seen_at = max(_as_utc(incident.last_seen_at), _as_utc(event.timestamp))
    db.add(IncidentEvent(incident_id=incident.id, event_id=event.id))
    return incident


def _create_alert_if_required(db: DBSession, incident: Incident) -> Alert | None:
    should_alert = incident.risk_score >= 80 or "BRUTE_FORCE" in incident.attack_type
    if not should_alert:
        return None
    existing = db.scalar(
        select(Alert).where(Alert.incident_id == incident.id, Alert.status != AlertStatus.RESOLVED)
    )
    if existing:
        existing.severity = incident.severity
        return existing
    alert = Alert(
        incident_id=incident.id,
        title=f"{incident.attack_type} from {incident.source_ip}",
        severity=incident.severity,
    )
    db.add(alert)
    db.flush()
    return alert


def _enqueue_background_work(event_id: str, source_ip: str) -> None:
    settings = get_settings()
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25)
        client.xadd(
            "honeypot:jobs",
            {"kind": "enrich_event", "event_id": event_id, "source_ip": source_ip},
            maxlen=100_000,
            approximate=True,
        )
        client.publish("honeypot:events", json.dumps({"event_id": event_id}))
        client.close()
    except Exception:
        # PostgreSQL remains authoritative. The worker health endpoint exposes a
        # Redis outage and the event can be replayed later without data loss.
        return
