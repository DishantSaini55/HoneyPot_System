from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import verify_sensor_key
from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.events import EventIngestResponse, EventRead, EventCreate
from app.services.ingestion import ingest_event


router = APIRouter(prefix="/ingest", tags=["sensor ingestion"], dependencies=[Depends(verify_sensor_key)])


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

