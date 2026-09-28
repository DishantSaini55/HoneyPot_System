from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator


class EventCreate(BaseModel):
    event_id: str = Field(min_length=8, max_length=64)
    timestamp: datetime
    source_ip: IPvAnyAddress
    source_port: int | None = Field(default=None, ge=1, le=65535)
    destination_port: int = Field(ge=1, le=65535)
    protocol: str = Field(min_length=2, max_length=16)
    honeypot: str = Field(min_length=2, max_length=32)
    session_id: str = Field(min_length=8, max_length=64)
    event_type: str = Field(min_length=3, max_length=64)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=4096)
    command: str | None = Field(default=None, max_length=16_384)
    simulated_response: str | None = Field(default=None, max_length=65_536)
    user_agent: str | None = Field(default=None, max_length=4096)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("protocol", "honeypot", "event_type")
    @classmethod
    def normalize_upper(cls, value: str) -> str:
        return value.strip().upper()


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_id: str
    attack_type: str
    score: int
    evidence: dict[str, Any]


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    source_ip: str
    source_port: int | None
    destination_port: int
    protocol: str
    honeypot: str
    session_id: str
    event_type: str
    username: str | None
    command: str | None
    user_agent: str | None
    payload: dict[str, Any]
    severity: str
    risk_score: int
    detections: list[DetectionRead] = Field(default_factory=list)


class EventIngestResponse(BaseModel):
    event: EventRead
    incident_id: str | None
    alert_id: str | None
    duplicate: bool = False

