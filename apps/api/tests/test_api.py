from datetime import UTC, datetime


SENSOR_HEADERS = {"X-Sensor-Key": "test-sensor-key-at-least-24-characters"}


def test_sensor_authentication_is_required(client):
    response = client.post("/api/v1/ingest/events", json={})
    assert response.status_code == 401


def test_http_event_is_persisted_detected_and_correlated(client):
    payload = {
        "event_id": "event-http-0001",
        "timestamp": datetime.now(UTC).isoformat(),
        "source_ip": "192.0.2.55",
        "source_port": 52341,
        "destination_port": 8080,
        "protocol": "HTTP",
        "honeypot": "HTTP",
        "session_id": "session-http-0001",
        "event_type": "HTTP_REQUEST",
        "user_agent": "sqlmap/1.8",
        "payload": {
            "method": "GET",
            "path": "/../../etc/passwd",
            "raw_target": "/..%2f..%2fetc/passwd?id=1%20OR%201=1--",
            "query": {"id": "1 OR 1=1--"},
            "headers": {"user-agent": "sqlmap/1.8"},
            "body_size": 0,
            "response_code": 404,
        },
    }
    response = client.post("/api/v1/ingest/events", headers=SENSOR_HEADERS, json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["event"]["risk_score"] >= 80
    assert body["event"]["severity"] == "CRITICAL"
    assert body["incident_id"] is not None
    assert body["alert_id"] is not None
    assert {item["attack_type"] for item in body["event"]["detections"]} >= {
        "PATH_TRAVERSAL",
        "SQL_INJECTION",
        "SCANNER",
    }

    duplicate = client.post("/api/v1/ingest/events", headers=SENSOR_HEADERS, json=payload)
    assert duplicate.status_code == 202
    assert duplicate.json()["duplicate"] is True

    payload["event_id"] = "event-http-0002"
    payload["session_id"] = "session-http-0002"
    second = client.post("/api/v1/ingest/events", headers=SENSOR_HEADERS, json=payload)
    assert second.status_code == 202
    assert second.json()["incident_id"] == body["incident_id"]


def test_register_login_and_protected_management_api(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "a-secure-test-password"},
    )
    assert registered.status_code == 201
    assert registered.json()["role"] == "ADMIN"
    invalid = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    assert invalid.status_code == 401
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "a-secure-test-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    events = client.get("/api/v1/management/events", headers={"Authorization": f"Bearer {token}"})
    assert events.status_code == 200
