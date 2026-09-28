from datetime import UTC, datetime

from app.detectors.rules import DetectionContext, analyze_event, calculate_risk_score, severity_for_score
from app.schemas.events import EventCreate


def event(**overrides):
    values = {
        "event_id": "event-00000001",
        "timestamp": datetime.now(UTC),
        "source_ip": "192.0.2.10",
        "source_port": 42000,
        "destination_port": 8080,
        "protocol": "HTTP",
        "honeypot": "HTTP",
        "session_id": "session-00000001",
        "event_type": "HTTP_REQUEST",
        "user_agent": "sqlmap/1.8",
        "payload": {"path": "/../../etc/passwd", "raw_target": "/..%2f..%2fetc/passwd?id=1%20OR%201=1--"},
    }
    values.update(overrides)
    return EventCreate(**values)


def test_http_rules_are_based_on_real_payload_signals():
    results = analyze_event(event(), DetectionContext(recent_request_count=2))
    attack_types = {result.attack_type for result in results}
    assert {"PATH_TRAVERSAL", "SQL_INJECTION", "SCANNER"} <= attack_types
    score = calculate_risk_score(results)
    assert score >= 80
    assert severity_for_score(score) == "CRITICAL"


def test_fifth_auth_failure_triggers_brute_force():
    auth = event(protocol="SSH", honeypot="SSH", event_type="LOGIN_FAILURE", payload={})
    results = analyze_event(auth, DetectionContext(recent_auth_failures=5))
    assert [result.attack_type for result in results] == ["BRUTE_FORCE"]


def test_benign_event_has_zero_score():
    benign = event(user_agent="Mozilla/5.0", payload={"path": "/robots.txt", "raw_target": "/robots.txt"})
    results = analyze_event(benign, DetectionContext())
    assert results == []
    assert calculate_risk_score(results) == 0

