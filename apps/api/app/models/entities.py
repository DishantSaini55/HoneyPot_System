import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class RoleName(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    role: Mapped[Role] = relationship(back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class HoneypotNode(Base):
    __tablename__ = "honeypot_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    listen_port: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Attacker(Base):
    __tablename__ = "attackers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    source_ip: Mapped[str] = mapped_column(String(45), unique=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    asn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sessions: Mapped[list["Session"]] = relationship(back_populates="attacker")


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attacker_id: Mapped[str] = mapped_column(ForeignKey("attackers.id"), index=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("honeypot_nodes.id"), index=True)
    protocol: Mapped[str] = mapped_column(String(16), index=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int] = mapped_column(Integer)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.ACTIVE, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attacker: Mapped[Attacker] = relationship(back_populates="sessions")
    events: Mapped[list["Event"]] = relationship(back_populates="session")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_timestamp_type", "timestamp", "event_type"),
        Index("ix_events_source_ip_timestamp", "source_ip", "timestamp"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_ip: Mapped[str] = mapped_column(String(45), index=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int] = mapped_column(Integer)
    protocol: Mapped[str] = mapped_column(String(16), index=True)
    honeypot: Mapped[str] = mapped_column(String(32), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.LOW, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    session: Mapped[Session] = relationship(back_populates="events")
    detections: Mapped[list["Detection"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class CredentialCapture(Base):
    __tablename__ = "credential_captures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), unique=True)
    username: Mapped[str] = mapped_column(String(255))
    password_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    password_fingerprint: Mapped[str] = mapped_column(String(64))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CommandEvent(Base):
    __tablename__ = "command_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), unique=True)
    command: Mapped[str] = mapped_column(Text)
    simulated_response: Mapped[str | None] = mapped_column(Text, nullable=True)


class HttpRequest(Base):
    __tablename__ = "http_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), unique=True)
    method: Mapped[str] = mapped_column(String(16), index=True)
    path: Mapped[str] = mapped_column(Text, index=True)
    query: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    headers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    referer: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_size: Mapped[int] = mapped_column(Integer, default=0)
    response_code: Mapped[int] = mapped_column(Integer)


class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(String(80), index=True)
    attack_type: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    event: Mapped[Event] = relationship(back_populates="detections")


class ThreatIntel(Base):
    __tablename__ = "threat_intel"
    __table_args__ = (UniqueConstraint("source_ip", "provider", name="uq_threat_intel_ip_provider"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    source_ip: Mapped[str] = mapped_column(String(45), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    reputation_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    known_malicious: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="UNAVAILABLE")
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    incident_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, autoincrement=True)
    source_ip: Mapped[str] = mapped_column(String(45), index=True)
    attack_type: Mapped[str] = mapped_column(String(255), index=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), index=True)
    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    assigned_to_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[Severity] = mapped_column(Enum(Severity), index=True)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.NEW, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    minimum_score: Mapped[int] = mapped_column(Integer, default=80)
    attack_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    channels: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["IN_APP"])


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    model_version: Mapped[str] = mapped_column(String(120))
    classification: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="IN_APP")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

