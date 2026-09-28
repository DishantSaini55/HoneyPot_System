import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx


logger = logging.getLogger("honeypot.sensor")


@dataclass
class EventEnvelope:
    source_ip: str
    destination_port: int
    protocol: str
    honeypot: str
    session_id: str
    event_type: str
    source_port: int | None = None
    username: str | None = None
    password: str | None = None
    command: str | None = None
    simulated_response: str | None = None
    user_agent: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class EventClient:
    def __init__(self, ingestion_url: str | None = None, sensor_api_key: str | None = None) -> None:
        self.ingestion_url = ingestion_url or os.environ["INGESTION_URL"]
        self.sensor_api_key = sensor_api_key or os.environ["SENSOR_API_KEY"]
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def send(self, event: EventEnvelope) -> bool:
        for attempt in range(3):
            try:
                response = await self._client.post(
                    self.ingestion_url,
                    headers={"X-Sensor-Key": self.sensor_api_key},
                    json=event.as_payload(),
                )
                response.raise_for_status()
                return True
            except (httpx.HTTPError, OSError) as exc:
                if attempt == 2:
                    logger.error(
                        json.dumps(
                            {
                                "timestamp": datetime.now(UTC).isoformat(),
                                "service": "sensor",
                                "event": "ingestion_failed",
                                "event_id": event.event_id,
                                "error": type(exc).__name__,
                            }
                        )
                    )
                    return False
                await asyncio.sleep(0.25 * (2**attempt))
        return False

    async def heartbeat(self, name: str, kind: str, listen_port: int) -> bool:
        url = self.ingestion_url.rsplit("/", 1)[0] + "/heartbeat"
        try:
            response = await self._client.post(
                url,
                headers={"X-Sensor-Key": self.sensor_api_key},
                json={"name": name, "kind": kind, "listen_port": listen_port},
            )
            response.raise_for_status()
            return True
        except (httpx.HTTPError, OSError):
            return False

    async def heartbeat_loop(self, name: str, kind: str, listen_port: int, interval: int = 10) -> None:
        while True:
            await self.heartbeat(name, kind, listen_port)
            await asyncio.sleep(interval)

    async def close(self) -> None:
        await self._client.aclose()
