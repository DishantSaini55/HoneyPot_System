from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import verify_sensor_key
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.events import EventIngestResponse, EventRead, EventCreate
from app.models.entities import HoneypotNode
from app.services.ingestion import ingest_event


router = APIRouter(prefix="/ingest", tags=["sensor ingestion"], dependencies=[Depends(verify_sensor_key)])


class SensorHeartbeat(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(min_length=1, max_length=32)
    listen_port: int = Field(ge=1, le=65535)


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def sensor_heartbeat(payload: SensorHeartbeat, db: Session = Depends(get_db)) -> None:
    node = db.scalar(select(HoneypotNode).where(HoneypotNode.name == payload.name))
    if node is None:
        node = HoneypotNode(name=payload.name, kind=payload.kind.upper(), listen_port=payload.listen_port)
        db.add(node)
    node.kind = payload.kind.upper()
    node.listen_port = payload.listen_port
    node.last_seen_at = datetime.now(UTC)
    db.commit()


@router.post("/events", response_model=EventIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def create_event(payload: EventCreate, request: Request, db: Session = Depends(get_db)) -> EventIngestResponse:
    content_length = int(request.headers.get("content-length", "0") or 0)
    if content_length > get_settings().max_event_body_bytes:
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail="Event payload is too large")
    result = ingest_event(db, payload)
    return EventIngestResponse(
        event=EventRead.model_validate(result.event),
        incident_id=result.incident.id if result.incident else None,
        alert_id=result.alert.id if result.alert else None,
        duplicate=result.duplicate,
    )
