from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from ml.features import extract_from_events, vectorize


def test_extracts_incident_features() -> None:
    start = datetime.now(UTC)
    events = [
        SimpleNamespace(event_type="LOGIN_FAILURE", protocol="SSH", command=None, payload={}, timestamp=start, detections=[1]),
        SimpleNamespace(event_type="COMMAND", protocol="SSH", command="wget http://x", payload={}, timestamp=start + timedelta(seconds=30), detections=[1, 2]),
    ]
    features = extract_from_events(events)
    assert features["failed_login_count"] == 1
    assert features["suspicious_command_count"] == 1
    assert features["known_attack_pattern_count"] == 3
    assert len(vectorize(features)) == 8
