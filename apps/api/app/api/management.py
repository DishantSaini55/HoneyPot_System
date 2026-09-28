import asyncio
import csv
import io
import json
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import current_user, require_roles
from app.core.database import SessionLocal, get_db
from app.core.config import get_settings
from app.core.security import hash_password
from app.models.entities import (
    Alert,
    AlertStatus,
    Attacker,
    AuditLog,
    AlertRule,
    Detection,
    Event,
    HoneypotNode,
    HttpRequest,
    Incident,
    IncidentEvent,
    IncidentStatus,
    MLPrediction,
    CommandEvent,
    Role,
    RoleName,
    Session as HoneypotSession,
    SessionStatus,
    Severity,
    ThreatIntel,
    User,
)
from app.schemas.events import EventRead
from app.schemas.incidents import IncidentRead, IncidentUpdate


router = APIRouter(prefix="/management", tags=["management"], dependencies=[Depends(current_user)])


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: RoleName = RoleName.VIEWER


class AdminUserUpdate(BaseModel):
    role: RoleName | None = None
    is_active: bool | None = None


class AlertRuleWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    minimum_score: int = Field(ge=0, le=100)
    attack_type: str | None = Field(default=None, max_length=80)
    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["IN_APP"])


class AnalystQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=1_000)


@router.get("/events")
def list_events(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    search: str | None = None,
    severity: Severity | None = None,
    attack_type: str | None = None,
    honeypot: str | None = None,
    source_ip: str | None = None,
    session_id: str | None = None,
    endpoint: str | None = None,
    country: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Event).options(selectinload(Event.detections))
    count_stmt = select(func.count(func.distinct(Event.id)))
    filters = []
    if search:
        like = f"%{search}%"
        filters.append(
            or_(
                Event.id.ilike(like),
                Event.source_ip.ilike(like),
                Event.session_id.ilike(like),
                Event.command.ilike(like),
            )
        )
    if severity:
        filters.append(Event.severity == severity)
    if honeypot:
        filters.append(Event.honeypot == honeypot.upper())
    if source_ip:
        filters.append(Event.source_ip == source_ip)
    if session_id:
        filters.append(Event.session_id == session_id)
    if date_from:
        filters.append(Event.timestamp >= date_from)
    if date_to:
        filters.append(Event.timestamp <= date_to)
    if attack_type:
        stmt = stmt.join(Detection).where(Detection.attack_type == attack_type)
        count_stmt = count_stmt.join(Detection).where(Detection.attack_type == attack_type)
    if endpoint:
        stmt = stmt.join(HttpRequest).where(HttpRequest.path.ilike(f"%{endpoint}%"))
        count_stmt = count_stmt.join(HttpRequest).where(HttpRequest.path.ilike(f"%{endpoint}%"))
    if country:
        stmt = stmt.join(HoneypotSession, HoneypotSession.id == Event.session_id).join(Attacker).where(Attacker.country == country.upper())
        count_stmt = count_stmt.join(HoneypotSession, HoneypotSession.id == Event.session_id).join(Attacker).where(Attacker.country == country.upper())
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.order_by(desc(Event.timestamp)).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {"items": [EventRead.model_validate(item) for item in items], "page": page, "page_size": page_size, "total": total}


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: str, db: Session = Depends(get_db)) -> EventRead:
    event = db.scalar(select(Event).options(selectinload(Event.detections)).where(Event.id == event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventRead.model_validate(event)


@router.get("/incidents")
def list_incidents(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    status: IncidentStatus | None = None,
    severity: Severity | None = None,
    source_ip: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    filters = []
    if status:
        filters.append(Incident.status == status)
    if severity:
        filters.append(Incident.severity == severity)
    if source_ip:
        filters.append(Incident.source_ip == source_ip)
    stmt = select(Incident).where(*filters)
    total = db.scalar(select(func.count(Incident.id)).where(*filters)) or 0
    items = db.scalars(stmt.order_by(desc(Incident.last_seen_at)).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [IncidentRead.model_validate(item) for item in items], "page": page, "page_size": page_size, "total": total}


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)) -> dict:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = db.scalars(
        select(Event)
        .options(selectinload(Event.detections))
        .join(IncidentEvent, IncidentEvent.event_id == Event.id)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(Event.timestamp)
    ).unique().all()
    predictions = db.scalars(select(MLPrediction).where(MLPrediction.incident_id == incident_id).order_by(desc(MLPrediction.created_at))).all()
    return {
        "incident": IncidentRead.model_validate(incident),
        "events": [EventRead.model_validate(e) for e in events],
        "ml_predictions": [
            {"model_version": item.model_version, "classification": item.classification, "confidence": item.confidence, "features": item.features, "created_at": item.created_at}
            for item in predictions
        ],
    }


@router.post("/incidents/{incident_id}/analysis")
def analyze_incident_with_ai(
    incident_id: str,
    payload: AnalystQuestion,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
) -> dict:
    settings = get_settings()
    if not settings.ai_provider_url or not settings.ai_api_key or not settings.ai_model:
        raise HTTPException(status_code=503, detail="AI analyst is not configured")
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = db.scalars(
        select(Event).options(selectinload(Event.detections)).join(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(Event.timestamp)
    ).unique().all()
    evidence = {
        "incident": IncidentRead.model_validate(incident).model_dump(mode="json"),
        "events": [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "protocol": event.protocol,
                "command": event.command,
                "path": event.payload.get("path"),
                "detections": [item.attack_type for item in event.detections],
            }
            for event in events
        ],
    }
    try:
        response = httpx.post(
            settings.ai_provider_url,
            headers={"Authorization": f"Bearer {settings.ai_api_key.get_secret_value()}"},
            json={
                "model": settings.ai_model,
                "messages": [
                    {"role": "system", "content": "Analyze only the supplied honeypot incident evidence. State uncertainty and do not invent facts."},
                    {"role": "user", "content": payload.question + "\nEvidence:\n" + json.dumps(evidence)},
                ],
            },
            timeout=15.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="AI provider failed") from exc
    return {"label": "AI-generated analysis", "answer": content, "incident_id": incident_id}


@router.patch("/incidents/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
) -> IncidentRead:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    changes = payload.model_dump(exclude_unset=True)
    if payload.assigned_to_id is not None and db.get(User, payload.assigned_to_id) is None:
        raise HTTPException(status_code=422, detail="Assignee not found")
    for field, value in changes.items():
        setattr(incident, field, value)
    action = {
        IncidentStatus.ACKNOWLEDGED: "INCIDENT_ACKNOWLEDGED",
        IncidentStatus.RESOLVED: "INCIDENT_RESOLVED",
        IncidentStatus.NEW: "INCIDENT_REOPENED",
    }.get(payload.status, "INCIDENT_UPDATED")
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            source_ip=request.client.host if request.client else None,
            metadata_json={"incident_id": incident_id, "changes": {key: str(value) for key, value in changes.items()}},
        )
    )
    if payload.status == IncidentStatus.ACKNOWLEDGED:
        for alert in db.scalars(select(Alert).where(Alert.incident_id == incident_id)).all():
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(UTC)
    elif payload.status == IncidentStatus.RESOLVED:
        for alert in db.scalars(select(Alert).where(Alert.incident_id == incident_id)).all():
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(UTC)
    db.commit()
    db.refresh(incident)
    return IncidentRead.model_validate(incident)


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)) -> list[dict]:
    alerts = db.scalars(select(Alert).order_by(desc(Alert.created_at)).limit(200)).all()
    return [
        {
            "id": alert.id,
            "incident_id": alert.incident_id,
            "title": alert.title,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at,
        }
        for alert in alerts
    ]


@router.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db)) -> dict:
    severity_rows = db.execute(select(Event.severity, func.count(Event.id)).group_by(Event.severity)).all()
    category_rows = db.execute(select(Detection.attack_type, func.count(Detection.id)).group_by(Detection.attack_type)).all()
    bucket = (
        func.date_trunc("hour", Event.timestamp)
        if db.bind is not None and db.bind.dialect.name == "postgresql"
        else func.strftime("%Y-%m-%d %H:00:00", Event.timestamp)
    )
    timeline_rows = db.execute(
        select(bucket.label("bucket"), func.count(Event.id))
        .group_by("bucket")
        .order_by(desc("bucket"))
        .limit(48)
    ).all()
    total_events = db.scalar(select(func.count(Event.id))) or 0
    detected_events = db.scalar(select(func.count(func.distinct(Detection.event_id)))) or 0
    top_attackers = db.execute(select(Event.source_ip, func.count(Event.id)).group_by(Event.source_ip).order_by(desc(func.count(Event.id))).limit(10)).all()
    top_paths = db.execute(select(HttpRequest.path, func.count(HttpRequest.id)).group_by(HttpRequest.path).order_by(desc(func.count(HttpRequest.id))).limit(10)).all()
    top_commands = db.execute(select(CommandEvent.command, func.count(CommandEvent.id)).group_by(CommandEvent.command).order_by(desc(func.count(CommandEvent.id))).limit(10)).all()
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        duration_expression = func.extract("epoch", HoneypotSession.ended_at - HoneypotSession.started_at)
    else:
        duration_expression = (func.julianday(HoneypotSession.ended_at) - func.julianday(HoneypotSession.started_at)) * 86400
    average_duration = db.scalar(select(func.avg(duration_expression)).where(HoneypotSession.ended_at.is_not(None)))
    return {
        "total_events": total_events,
        "active_sessions": db.scalar(select(func.count(HoneypotSession.id)).where(HoneypotSession.status == SessionStatus.ACTIVE)) or 0,
        "unique_attackers": db.scalar(select(func.count(Attacker.id))) or 0,
        "critical_incidents": db.scalar(select(func.count(Incident.id)).where(Incident.severity == Severity.CRITICAL)) or 0,
        "detection_count": db.scalar(select(func.count(Detection.id))) or 0,
        "alert_count": db.scalar(select(func.count(Alert.id))) or 0,
        "authentication_failures": db.scalar(select(func.count(Event.id)).where(Event.event_type.in_(["LOGIN_ATTEMPT", "LOGIN_FAILURE", "AUTH_FAILURE"]))) or 0,
        "average_session_duration_seconds": round(float(average_duration), 2) if average_duration is not None else None,
        "detection_rate": round(detected_events / total_events, 4) if total_events else None,
        "top_attackers": [{"source_ip": key, "count": count} for key, count in top_attackers],
        "top_targeted_endpoints": [{"path": key, "count": count} for key, count in top_paths],
        "top_commands": [{"command": key, "count": count} for key, count in top_commands],
        "severity": {key.value: count for key, count in severity_rows},
        "categories": {key: count for key, count in category_rows},
        "timeline": [{"bucket": bucket, "count": count} for bucket, count in reversed(timeline_rows)],
    }


@router.get("/honeypots")
def list_honeypots(db: Session = Depends(get_db)) -> list[dict]:
    nodes = db.scalars(select(HoneypotNode).order_by(HoneypotNode.name)).all()
    return [
        {
            "id": node.id,
            "name": node.name,
            "kind": node.kind,
            "listen_port": node.listen_port,
            "enabled": node.enabled,
            "last_seen_at": node.last_seen_at,
        }
        for node in nodes
    ]


@router.get("/attackers")
def list_attackers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    filters = [Attacker.source_ip.ilike(f"%{search}%")] if search else []
    total = db.scalar(select(func.count(Attacker.id)).where(*filters)) or 0
    attackers = db.scalars(
        select(Attacker).where(*filters).order_by(desc(Attacker.last_seen_at)).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = []
    for attacker in attackers:
        session_count = db.scalar(select(func.count(HoneypotSession.id)).where(HoneypotSession.attacker_id == attacker.id)) or 0
        event_count = db.scalar(select(func.count(Event.id)).where(Event.source_ip == attacker.source_ip)) or 0
        max_risk = db.scalar(select(func.max(Event.risk_score)).where(Event.source_ip == attacker.source_ip)) or 0
        items.append(
            {
                "id": attacker.id,
                "source_ip": attacker.source_ip,
                "first_seen_at": attacker.first_seen_at,
                "last_seen_at": attacker.last_seen_at,
                "country": attacker.country,
                "city": attacker.city,
                "asn": attacker.asn,
                "organization": attacker.organization,
                "session_count": session_count,
                "event_count": event_count,
                "max_risk_score": max_risk,
            }
        )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/attackers-map")
def attacker_map(db: Session = Depends(get_db)) -> dict:
    located = db.scalars(select(Attacker).where(Attacker.latitude.is_not(None), Attacker.longitude.is_not(None))).all()
    unavailable = db.scalar(select(func.count(Attacker.id)).where(or_(Attacker.latitude.is_(None), Attacker.longitude.is_(None)))) or 0
    return {
        "points": [
            {
                "source_ip": item.source_ip,
                "country": item.country,
                "city": item.city,
                "latitude": item.latitude,
                "longitude": item.longitude,
            }
            for item in located
        ],
        "unavailable_count": unavailable,
    }


@router.get("/attackers/{source_ip}")
def get_attacker(source_ip: str, db: Session = Depends(get_db)) -> dict:
    attacker = db.scalar(select(Attacker).where(Attacker.source_ip == source_ip))
    if attacker is None:
        raise HTTPException(status_code=404, detail="Attacker not found")
    sessions = db.scalars(
        select(HoneypotSession).where(HoneypotSession.attacker_id == attacker.id).order_by(desc(HoneypotSession.started_at))
    ).all()
    intel = db.scalars(select(ThreatIntel).where(ThreatIntel.source_ip == source_ip)).all()
    return {
        "attacker": {
            "source_ip": attacker.source_ip,
            "first_seen_at": attacker.first_seen_at,
            "last_seen_at": attacker.last_seen_at,
            "country": attacker.country,
            "city": attacker.city,
            "latitude": attacker.latitude,
            "longitude": attacker.longitude,
            "asn": attacker.asn,
            "organization": attacker.organization,
        },
        "sessions": [
            {
                "id": item.id,
                "protocol": item.protocol,
                "source_port": item.source_port,
                "destination_port": item.destination_port,
                "status": item.status.value,
                "started_at": item.started_at,
                "ended_at": item.ended_at,
            }
            for item in sessions
        ],
        "threat_intelligence": [
            {"provider": item.provider, "status": item.status, "data": item.data, "checked_at": item.checked_at}
            for item in intel
        ],
    }


@router.get("/sessions")
def list_sessions(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
) -> dict:
    total = db.scalar(select(func.count(HoneypotSession.id))) or 0
    sessions = db.scalars(
        select(HoneypotSession).order_by(desc(HoneypotSession.started_at)).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = []
    for item in sessions:
        attacker = db.get(Attacker, item.attacker_id)
        count = db.scalar(select(func.count(Event.id)).where(Event.session_id == item.id)) or 0
        items.append(
            {
                "id": item.id,
                "source_ip": attacker.source_ip if attacker else "unknown",
                "protocol": item.protocol,
                "destination_port": item.destination_port,
                "status": item.status.value,
                "started_at": item.started_at,
                "ended_at": item.ended_at,
                "event_count": count,
            }
        )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)) -> dict:
    session = db.get(HoneypotSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    events = db.scalars(
        select(Event).options(selectinload(Event.detections)).where(Event.session_id == session_id).order_by(Event.timestamp)
    ).unique().all()
    return {
        "session": {
            "id": session.id,
            "protocol": session.protocol,
            "source_port": session.source_port,
            "destination_port": session.destination_port,
            "status": session.status.value,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
        },
        "events": [EventRead.model_validate(item) for item in events],
    }


@router.get("/threat-intelligence")
def list_threat_intelligence(db: Session = Depends(get_db)) -> list[dict]:
    records = db.scalars(select(ThreatIntel).order_by(desc(ThreatIntel.checked_at)).limit(500)).all()
    return [
        {
            "id": item.id,
            "source_ip": item.source_ip,
            "provider": item.provider,
            "status": item.status,
            "reputation_score": item.reputation_score,
            "known_malicious": item.known_malicious,
            "data": item.data,
            "checked_at": item.checked_at,
        }
        for item in records
    ]


@router.get("/admin/audit-logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ADMIN)),
) -> list[dict]:
    records = db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(500)).all()
    return [
        {"id": item.id, "user_id": item.user_id, "action": item.action, "source_ip": item.source_ip, "metadata": item.metadata_json, "created_at": item.created_at}
        for item in records
    ]


@router.get("/users/assignees")
def list_assignees(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
) -> list[dict]:
    users = db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.email)).all()
    return [{"id": item.id, "email": item.email, "role": item.role.name.value} for item in users]


@router.get("/admin/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ADMIN)),
) -> list[dict]:
    users = db.scalars(select(User).order_by(User.created_at)).all()
    return [
        {"id": item.id, "email": item.email, "role": item.role.name.value, "is_active": item.is_active, "created_at": item.created_at}
        for item in users
    ]


@router.post("/admin/users", status_code=201)
def create_user(
    payload: AdminUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(RoleName.ADMIN)),
) -> dict:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    role = db.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise HTTPException(status_code=400, detail="Unknown role")
    created = User(email=email, password_hash=hash_password(payload.password), role_id=role.id)
    db.add(created)
    db.flush()
    db.add(AuditLog(user_id=admin.id, action="USER_CREATED", source_ip=request.client.host if request.client else None, metadata_json={"created_user_id": created.id, "role": payload.role.value}))
    db.commit()
    return {"id": created.id, "email": created.email, "role": payload.role.value, "is_active": created.is_active}


@router.patch("/admin/users/{user_id}")
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(RoleName.ADMIN)),
) -> dict:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is not None:
        role = db.scalar(select(Role).where(Role.name == payload.role))
        if role is None:
            raise HTTPException(status_code=400, detail="Unknown role")
        target.role_id = role.id
    if payload.is_active is not None:
        if target.id == admin.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="Administrators cannot deactivate themselves")
        target.is_active = payload.is_active
    db.add(AuditLog(user_id=admin.id, action="USER_UPDATED", source_ip=request.client.host if request.client else None, metadata_json={"updated_user_id": target.id, "changes": payload.model_dump(exclude_unset=True, mode="json")}))
    db.commit()
    db.refresh(target)
    return {"id": target.id, "email": target.email, "role": target.role.name.value, "is_active": target.is_active}


@router.get("/admin/rules")
def list_rules(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
) -> list[dict]:
    rules = db.scalars(select(AlertRule).order_by(AlertRule.name)).all()
    return [
        {"id": item.id, "name": item.name, "minimum_score": item.minimum_score, "attack_type": item.attack_type, "enabled": item.enabled, "channels": item.channels}
        for item in rules
    ]


@router.post("/admin/rules", status_code=201)
def create_rule(
    payload: AlertRuleWrite,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleName.ADMIN)),
) -> dict:
    if db.scalar(select(AlertRule).where(AlertRule.name == payload.name)):
        raise HTTPException(status_code=409, detail="Rule name already exists")
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="RULE_CREATED", source_ip=request.client.host if request.client else None, metadata_json={"rule_id": rule.id}))
    db.commit()
    return {"id": rule.id, **payload.model_dump()}


@router.patch("/admin/rules/{rule_id}")
def update_rule(
    rule_id: str,
    payload: AlertRuleWrite,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleName.ADMIN)),
) -> dict:
    rule = db.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.add(AuditLog(user_id=user.id, action="RULE_UPDATED", source_ip=request.client.host if request.client else None, metadata_json={"rule_id": rule.id}))
    db.commit()
    return {"id": rule.id, **payload.model_dump()}


@router.get("/export/events")
def export_events(
    format: str = Query(pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
) -> Response:
    events = db.scalars(select(Event).order_by(Event.timestamp).limit(10_000)).all()
    rows = [
        {
            "event_id": item.id,
            "timestamp": item.timestamp.isoformat(),
            "source_ip": item.source_ip,
            "protocol": item.protocol,
            "honeypot": item.honeypot,
            "session_id": item.session_id,
            "event_type": item.event_type,
            "severity": item.severity.value,
            "risk_score": item.risk_score,
            "command": item.command,
        }
        for item in events
    ]
    db.add(AuditLog(user_id=user.id, action="EXPORT_CREATED", metadata_json={"format": format, "count": len(rows)}))
    db.commit()
    if format == "json":
        return Response(
            json.dumps(rows, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="events.json"'},
        )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else ["event_id"])
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="events.csv"'},
    )


@router.get("/stream/events")
async def stream_events(after: datetime | None = None) -> StreamingResponse:
    async def generate():
        cursor = after or datetime.now(UTC)
        while True:
            with SessionLocal() as db:
                events = db.scalars(select(Event).where(Event.timestamp > cursor).order_by(Event.timestamp).limit(100)).all()
                for event in events:
                    cursor = max(cursor, event.timestamp.replace(tzinfo=UTC) if event.timestamp.tzinfo is None else event.timestamp)
                    payload = {
                        "id": event.id,
                        "timestamp": event.timestamp.isoformat(),
                        "source_ip": event.source_ip,
                        "event_type": event.event_type,
                        "severity": event.severity.value,
                        "risk_score": event.risk_score,
                    }
                    yield f"event: telemetry\ndata: {json.dumps(payload)}\n\n"
            yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
