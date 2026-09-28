# Verification report

Verification date: 2026-09-29. Environment: Windows development host, Python 3.12, Node.js, no Docker executable installed.

| Feature | Status | Evidence |
|---|---|---|
| Frontend | PASS | ESLint, TypeScript, optimized Next.js build, and Playwright analyst flow passed; 24 routes generated. |
| Backend | PASS | Ruff passed; API tests passed. |
| Database | PASS | SQLite migration upgrade/downgrade smoke passed; live persistence restart was exercised. PostgreSQL container was not runnable on this host. |
| Redis | NOT RUN | Integration code and health checks exist; Docker/Redis unavailable on this host. |
| SSH honeypot | PASS | Unit tests passed and a local SSH-to-ingestion vertical test persisted events. |
| HTTP honeypot | PASS | Unit tests passed and local probes persisted/detected events. |
| Detection | PASS | Rule tests and live SQLi/traversal/scanner/brute-force/command flow passed. |
| ML | PASS | Model trained, evaluation JSON generated, feature test passed, and an actual brute-force probability was produced. Metrics are synthetic-only. |
| Threat intelligence | PARTIAL | Failure/no-provider paths implemented; no external provider key was supplied. |
| Alerts | PASS | Critical correlated live flow created a persisted alert; in-app/webhook worker path implemented. |
| Authentication | PASS | Invalid login, protected route, expired token, role restriction, refresh/logout architecture tested. |
| Real-time | PASS | SSE connections were exercised by the running dashboard during the browser E2E flow. |
| Analytics | PASS | SQL aggregation and portable local dashboard query implemented; frontend build passed. |
| Docker | NOT RUN | Compose and hardened Dockerfiles created; Docker is not installed on this host. |
| Tests | PASS | Root `pytest` passed: 10 API + 2 SSH + 3 HTTP + 1 ML tests. |
| CI/CD | PASS | CI and security workflow definitions added; remote GitHub execution is pending push. |
| Security isolation | PARTIAL | Configuration review passed; runtime network-isolation verification requires Docker. |

The Playwright test ran against a production Next.js server and a local SQLite-backed FastAPI process. It registered/logged in, ingested a real high-risk HTTP event, opened its correlated incident, acknowledged it, and resolved it successfully.

`PASS` means executed locally. `PARTIAL` and `NOT RUN` are intentionally not presented as successful runtime validation.
