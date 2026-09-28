"""Generate explicit load-test telemetry and report measured client throughput."""
import argparse
import time
import uuid
from datetime import UTC, datetime

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--url", default="http://localhost:8000/api/v1/ingest/events")
    parser.add_argument("--sensor-key", required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    failures = 0
    latencies: list[float] = []
    with httpx.Client(timeout=10) as client:
        for index in range(args.count):
            request_started = time.perf_counter()
            response = client.post(
                args.url,
                headers={"X-Sensor-Key": args.sensor_key},
                json={
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "source_ip": f"192.0.2.{index % 250 + 1}",
                    "source_port": 40000 + index % 20000,
                    "destination_port": 8080,
                    "protocol": "HTTP",
                    "honeypot": "HTTP",
                    "session_id": str(uuid.uuid4()),
                    "event_type": "HTTP_REQUEST",
                    "user_agent": "honeypot-load-generator/1.0",
                    "payload": {"method": "GET", "path": "/admin", "query": {}, "headers": {}, "body_size": 0, "response_code": 200, "load_test": True},
                },
            )
            latencies.append(time.perf_counter() - request_started)
            failures += int(response.status_code >= 400)
    elapsed = time.perf_counter() - started
    print({"attempted": args.count, "failures": failures, "elapsed_seconds": round(elapsed, 3), "events_per_second": round(args.count / elapsed, 2), "average_request_ms": round(sum(latencies) / len(latencies) * 1000, 2)})


if __name__ == "__main__":
    main()
