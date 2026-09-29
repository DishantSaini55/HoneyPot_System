# Native runtime verification report

Verification date: 2026-09-29.

## Executive Summary

The application was run without Docker on a Windows development host using a repository-local PostgreSQL 18.4 server and native Redis 8.10.1 for Windows. FastAPI, the Redis Streams worker, the isolated SSH and HTTP decoys, and a production Next.js standalone server ran together. Authenticated ingestion persisted events to PostgreSQL, published Redis Stream jobs, and the worker consumed every delivered job. The browser suite verified login, a live dashboard update without refresh, incident acknowledgement/resolution, and every major SOC route.

Docker was not installed or used for this validation.

## Environment

| Component | Version / configuration |
|---|---|
| OS | Windows development host |
| Python | 3.12.10 |
| Node.js | 22.20.0 |
| npm | 10.9.3 |
| PostgreSQL | 18.4, native repository-local cluster at `127.0.0.1:55432` |
| Redis | 8.10.1 native Windows build at `127.0.0.1:56379` |

Runtime evidence: Alembic revision `0002`, 21 public tables, 81 indexes, 172 persisted events, 89 detections, 17 incidents, 6 alerts, 23 audit-log entries, 14 refresh-token rows, 2 reset-token rows, 17 ML predictions, and 15 threat-intelligence status rows. Redis Streams showed 172 entries, one worker consumer, zero pending entries, and zero lag.

## Test Results

| Test | Result | Evidence |
|---|---|---|
| Ruff | PASS | `python -m ruff check apps packages ml scripts` reported all checks passed. |
| Pytest | PASS | 17 passed: API, rules, virtual shell, HTTP decoy, and ML feature tests. |
| Alembic | PASS | Native PostgreSQL `alembic upgrade head`; database reported revision `0002`. |
| ESLint | PASS | `npm.cmd run lint` after generated Playwright directories were excluded. |
| TypeScript | PASS | `npm.cmd run typecheck`. |
| Next.js Build | PASS | `npm.cmd run build`; 19 routes generated. |
| Playwright | PASS | 2 passed in 36.0 seconds against native PostgreSQL/Redis/API/worker/decoys and standalone Next.js. |
| npm audit | PASS | 0 vulnerabilities in the web application and native PostgreSQL tooling packages. |
| PostgreSQL | PASS | Native connection, migration, 21 tables, 81 indexes, and persistence through ingestion/auth/workflows. |
| Redis | PASS | Native Redis PING, Streams XADD/XRANGE, ingestion publishing, worker consumption, zero pending jobs. |
| SSH Honeypot | PASS | Listener, auth, virtual commands, ingestion, detection, worker delivery, and host-escape negative test passed. |
| HTTP Honeypot | PASS | Local login, traversal, SQLi, command-injection, scanner, and malformed probes reached ingestion. |
| Detection | PASS | All 13 deterministic rules were exercised through live authenticated ingestion. |
| Incidents | PASS | Events created incidents/alerts; a live incident transitioned NEW → ACKNOWLEDGED → RESOLVED with audit entries. |
| SSE | PASS | Playwright ingested an event after dashboard load and observed the total-event count update without refresh. |
| Authentication | PASS | Invalid login, login, protected-route denial, refresh rotation, logout revocation, reset request persistence, and invalid reset rejection tested live. |
| RBAC | PASS | VIEWER could read events but received 403 from administration APIs; ADMIN workflow passed. |
| ML Pipeline | PASS | Training/evaluation, model persistence/load, worker prediction, and prediction persistence executed. |
| SOC Dashboard | PASS | Major SOC pages rendered from backend APIs in browser validation. |

## Detection results

| Detection | Triggered | Score | Severity | Incident | Alert | Status |
|---|---:|---:|---|---:|---:|---|
| SSH-CMD-WGET | YES | 35 | MEDIUM | YES | NO | PASS |
| SSH-CMD-CURL | YES | 30 | MEDIUM | YES | NO | PASS |
| SSH-CMD-CHMOD | YES | 35 | MEDIUM | YES | NO | PASS |
| SSH-CMD-REVERSE_SHELL | YES | 60 | HIGH | YES | NO | PASS |
| SSH-CMD-SCRIPT_EXEC | YES | 45 | MEDIUM | YES | NO | PASS |
| CRED-ACCESS-001 | YES | 40 | MEDIUM | YES | NO | PASS |
| WEB-SQLI-001 | YES | 55 | MEDIUM | YES | NO | PASS |
| WEB-TRAV-001 | YES | 50 | MEDIUM | YES | NO | PASS |
| WEB-CMDI-001 | YES | 55 | MEDIUM | YES | NO | PASS |
| WEB-UA-001 | YES | 25 | LOW | YES | NO | PASS |
| WEB-SCAN-001 | YES | 35 | MEDIUM | YES | NO | PASS |
| WEB-RATE-001 | YES | 45 | MEDIUM | YES | YES | PASS |
| AUTH-BRUTE-001 | YES | 55 | MEDIUM | YES | YES | PASS |

The alert result is the actual correlated-incident outcome. Lower-scored events normally create an incident but do not independently meet the alert threshold; correlation can raise an incident above it.

## Security Findings

### Critical

None found in this source/runtime review.

### High

None found in this source/runtime review.

### Medium

None open in the implemented authentication/reset controls. Production operators must still configure a private HTTPS reset-delivery endpoint and its secret.

### Low

- Sensor authentication is a shared API key. Rotate it on compromise and use isolated networks; per-sensor identities are a future hardening improvement.
- Native defaults bind management/data services to loopback. Any broader deployment must firewall management/API/database/Redis ports.

### Informational

- The SSH virtual shell uses an allowlisted dispatcher and never calls a host shell, subprocess, `eval`, or `os.system`. A live `cmd.exe` escape attempt returned `command not found` and created no marker file.
- SQLAlchemy uses parameterized ORM/database expressions. No unsafe deserialization or attacker-controlled filesystem path was found in the decoy flow.
- The HTTP decoy deliberately accepts untrusted requests; captured sensitive headers are redacted.
- No production frontend mock data was found. Remaining similar terms are tests, development data, configuration, or historical audit documentation.
- Login, reset request, and reset confirmation are now Redis-backed rate limited with a process-local outage fallback. Limits and window are environment-configurable.
- Reset delivery now signs canonical JSON with HMAC-SHA256, timestamp, and unique delivery ID. Production configuration rejects a non-HTTPS webhook or missing webhook secret.

## Architecture

`Next.js SOC dashboard -> Next BFF -> FastAPI -> PostgreSQL` is the management path. `SSH/HTTP decoys -> authenticated ingestion -> PostgreSQL + Redis Streams -> worker -> enrichment/ML/notifications` is the sensor path. Redis, PostgreSQL, workers, and decoys are internal services; the dashboard is the sole analyst UI. The only frontend in this repository is the production Next.js SOC dashboard. SSH and HTTP are intentionally simulated attacker-facing decoys, not administrative UIs. No Vite, Flask, duplicate dashboard, or mock production frontend remains.

## Threat Intelligence

The generic configured HTTP provider adapter is implemented. Its no-provider path was exercised live: worker jobs persisted `UNAVAILABLE` records and continued processing. No provider URL/API key was supplied, so no provider response was tested and no provider claims are made. There are no provider-specific adapters in this repository.

## ML

The logistic-regression model trained, persisted to `ml/model/baseline.joblib`, loaded in the worker, produced predictions, and persisted them. Development training data is synthetic and is used to validate pipeline functionality, not to establish real-world detection performance. Perfect synthetic metrics are not production accuracy evidence.

## Limitations

- No external threat-intelligence credentials were available.
- Password-reset delivery to an actual webhook was not exercised. One-time confirmation is unit-tested with deterministic mocked delivery; live native runtime verified request persistence and invalid-token handling.
- Empty/loading/error dashboard components were inspected and retained; browser validation exercised populated states. A deliberate API-outage error UI test was not run.
- Docker/container network isolation, TLS proxy, and hardened container runtime were not tested because Docker was intentionally not installed or used.
- This is not an independent penetration test.
- The API-failure UI and SSE reconnect paths are covered by Playwright source tests; their final native browser execution is pending the next complete stack regression after this security hardening change.

## Docker

Docker is not required for local development or validation. Container configuration remains available for optional production deployment but was not used for local runtime validation.

## Final Status

**MOSTLY VALIDATED**

The native core runtime is validated end to end. The status is intentionally not `FULLY VALIDATED NATIVE RUNTIME` because provider-backed threat intelligence, actual password-reset delivery, deliberate dashboard error-state injection, and optional container/TLS runtime testing remain outside the executed evidence.
