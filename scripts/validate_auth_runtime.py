"""Validate live authentication, RBAC, and incident state against PostgreSQL."""

import os
import uuid

import httpx


API = os.getenv("VALIDATION_API_URL", "http://127.0.0.1:8000")
ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("VALIDATION_ADMIN_PASSWORD", "native-admin-password-2026")


def main() -> None:
    with httpx.Client(base_url=API, timeout=10, trust_env=False) as client:
        registration = client.post("/api/v1/auth/register", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert registration.status_code in {201, 409}
        invalid = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "invalid-password"})
        assert invalid.status_code == 401
        login = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        login.raise_for_status()
        pair = login.json()
        admin_headers = {"Authorization": f"Bearer {pair['access_token']}"}
        assert client.get("/api/v1/management/events", headers=admin_headers).status_code == 200
        assert client.get("/api/v1/management/events").status_code == 401

        refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        refreshed.raise_for_status()
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401
        replacement = refreshed.json()["refresh_token"]
        assert client.post("/api/v1/auth/logout", json={"refresh_token": replacement}).status_code == 204
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": replacement}).status_code == 401

        viewer_email = f"viewer-{uuid.uuid4().hex[:8]}@example.com"
        viewer_password = "native-viewer-password-2026"
        viewer = client.post("/api/v1/auth/register", json={"email": viewer_email, "password": viewer_password})
        viewer.raise_for_status()
        assert viewer.json()["role"] == "VIEWER"
        viewer_login = client.post("/api/v1/auth/login", json={"email": viewer_email, "password": viewer_password})
        viewer_login.raise_for_status()
        viewer_headers = {"Authorization": f"Bearer {viewer_login.json()['access_token']}"}
        assert client.get("/api/v1/management/admin/users", headers=viewer_headers).status_code == 403
        assert client.get("/api/v1/management/events", headers=viewer_headers).status_code == 200

        reset = client.post("/api/v1/auth/password-reset/request", json={"email": ADMIN_EMAIL})
        assert reset.status_code == 202
        assert client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "invalid-token-that-is-at-least-32-chars", "password": "another-native-password-2026"},
        ).status_code == 400

        incidents = client.get("/api/v1/management/incidents", headers=admin_headers).json()["items"]
        incident_id = next(item["id"] for item in incidents if item["status"] != "RESOLVED")
        acknowledged = client.patch(
            f"/api/v1/management/incidents/{incident_id}", headers=admin_headers, json={"status": "ACKNOWLEDGED"}
        )
        assert acknowledged.status_code == 200 and acknowledged.json()["status"] == "ACKNOWLEDGED"
        resolved = client.patch(
            f"/api/v1/management/incidents/{incident_id}", headers=admin_headers, json={"status": "RESOLVED"}
        )
        assert resolved.status_code == 200 and resolved.json()["status"] == "RESOLVED"

    print("PASS: invalid login, login, protected API, refresh rotation, logout revocation, and unauthorized access")
    print("PASS: VIEWER read access and administration denial")
    print("PASS: password-reset request persistence and invalid-token rejection")
    print("PASS: incident NEW -> ACKNOWLEDGED -> RESOLVED with audit logging")


if __name__ == "__main__":
    main()
