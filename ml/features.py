from __future__ import annotations

from collections.abc import Iterable
from typing import Any


FEATURE_NAMES = [
    "failed_login_count",
    "request_count",
    "session_duration_seconds",
    "command_count",
    "suspicious_command_count",
    "unique_paths",
    "request_rate",
    "known_attack_pattern_count",
]


def vectorize(features: dict[str, Any]) -> list[float]:
    """Return a stable numeric feature vector in model training order."""
    return [float(features.get(name, 0) or 0) for name in FEATURE_NAMES]


def extract_from_events(events: Iterable[Any]) -> dict[str, float]:
    """Extract explainable aggregate features from Event-like objects."""
    rows = list(events)
    if not rows:
        return {name: 0.0 for name in FEATURE_NAMES}
    failures = sum(row.event_type in {"LOGIN_ATTEMPT", "LOGIN_FAILURE", "AUTH_FAILURE"} for row in rows)
    http_rows = [row for row in rows if row.protocol == "HTTP"]
    commands = [str(row.command or "").lower() for row in rows if row.command]
    suspicious = sum(any(token in command for token in ("wget", "curl", "chmod +x", "nc ", "bash -i")) for command in commands)
    paths = {str((row.payload or {}).get("path")) for row in http_rows if (row.payload or {}).get("path")}
    timestamps = sorted(row.timestamp for row in rows)
    duration = max(0.0, (timestamps[-1] - timestamps[0]).total_seconds())
    pattern_count = sum(len(getattr(row, "detections", []) or []) for row in rows)
    minutes = max(duration / 60.0, 1.0)
    return {
        "failed_login_count": float(failures),
        "request_count": float(len(http_rows)),
        "session_duration_seconds": duration,
        "command_count": float(len(commands)),
        "suspicious_command_count": float(suspicious),
        "unique_paths": float(len(paths)),
        "request_rate": float(len(http_rows)) / minutes,
        "known_attack_pattern_count": float(pattern_count),
    }
