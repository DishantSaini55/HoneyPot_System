from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import IncidentStatus, Severity


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_number: int
    source_ip: str
    attack_type: str
    severity: Severity
    risk_score: int
    status: IncidentStatus
    first_seen_at: datetime
    last_seen_at: datetime
    assigned_to_id: str | None
    note: str | None


class IncidentUpdate(BaseModel):
    status: IncidentStatus | None = None
    severity: Severity | None = None
    assigned_to_id: str | None = None
    note: str | None = Field(default=None, max_length=10_000)

