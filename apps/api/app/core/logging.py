import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "service": self.service,
                "level": record.levelname,
                "event": record.getMessage(),
            }
        )


def configure_logging(level: str, service: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service))
    logging.basicConfig(level=level, handlers=[handler], force=True)
