# HoneyPot System

A production-style, full-stack cybersecurity honeypot and threat-monitoring platform. Isolated SSH and HTTP decoys emit authenticated telemetry to FastAPI; PostgreSQL persists it; deterministic rules score and correlate attacks; Redis Streams drives enrichment, ML classification, and notifications; a Next.js SOC dashboard receives live events through SSE.

No production page falls back to mock data. Empty databases show an empty state.

## Architecture

```text
Internet -> SSH/HTTP decoys -> authenticated ingestion API -> PostgreSQL
                                      |                       |
                                      +-> Redis Streams -> worker
                                                           |-- threat intel
                                                           |-- baseline ML
                                                           +-- notifications

Analyst -> Next.js BFF -> authenticated management API -> analytics/SSE
```

Docker places the decoys only on the sensor network. PostgreSQL and Redis are only on the internal management network. The API is the sole bridge; decoys have no database credentials. Containers run as non-root, drop all capabilities, use `no-new-privileges`, process/resource limits, and read-only filesystems where practical.

## Implemented features

- Concurrent AsyncSSH decoy with a deterministic virtual shell that never invokes host commands.
- HTTP decoy capturing method, target, query, redacted headers, body size, response status, and session identity.
- Consistent event envelope, idempotent ingestion, sensor API key, payload limit, and rate limiting.
- PostgreSQL schema and Alembic migrations for users, roles, nodes, attackers, sessions, events, specialized telemetry, detections, intelligence, incidents, alerts, rules, ML predictions, audit logs, and notifications.
- Explainable rules for brute force, dangerous commands, credential access, scanning, SQL injection, traversal, injection, and scanner user agents.
- Transparent 0-100 scoring and 15-minute IP-based incident correlation.
- Optional provider-based IP enrichment with cache, timeout, retry, and failure isolation.
- Executable logistic-regression baseline with persisted predictions. Its bundled training set is explicitly synthetic development data; its metrics are not production accuracy claims.
- JWT access tokens, rotating refresh tokens, Argon2 password hashes, one-time password-reset tokens, and ADMIN/ANALYST/VIEWER authorization.
- Real database analytics, filters, pagination, CSV/JSON export, audit logs, SSE updates, system health, and an actual-coordinate attack plot.
- Optional OpenAI-compatible analyst endpoint grounded only in stored incident evidence.

## Stack

Next.js 16, React 19, TypeScript, Tailwind CSS, TanStack Query, Recharts, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis Streams, AsyncSSH, scikit-learn, Docker Compose, Pytest, Playwright, Ruff, and GitHub Actions.

## Quick start with Docker

Requirements: Docker Engine with Compose v2.

```bash
cp .env.example .env
# Replace every replace/change-me value with generated secrets.
docker compose up --build
```

Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Open `http://localhost:3000`, register the exact `BOOTSTRAP_ADMIN_EMAIL`, and the first matching account becomes ADMIN. API docs are disabled in production mode; for development set `ENVIRONMENT=development` and visit `http://localhost:8000/docs`.

Exercise the decoys:

```bash
ssh -p 2222 admin@localhost
curl http://localhost:8080/admin
curl http://localhost:8080/.env
curl "http://localhost:8080/..%2f..%2fetc/passwd"
```

Stop services with `docker compose down`. Add `-v` only when you intentionally want to destroy persisted PostgreSQL/Redis data.

## Local development

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt -r ml/requirements.txt
.venv\Scripts\python -m pip install -e packages/sensor-sdk -r apps/ssh-honeypot/requirements.txt -r apps/http-honeypot/requirements.txt
Copy-Item .env.example .env
cd apps/api
..\..\.venv\Scripts\python -m alembic upgrade head
..\..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd apps/web
npm ci
npm run dev
```

PostgreSQL and Redis are expected at the URLs in `.env`; Docker Compose is the simplest way to provide them. The sensors and worker can be started with their `main.py` entrypoints once the environment variables are loaded.

## Configuration

All variables are documented in [.env.example](.env.example). Required production values are `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, and `SENSOR_API_KEY`. Ports, token lifetimes, CORS, body/rate limits, threat-intel provider, webhook alerting, optional AI, model path, and logging are configurable. `.env` files are ignored by Git.

External intelligence, webhook, password-reset delivery, and AI calls are disabled unless their URLs/keys are configured. Their absence never disables deterministic detection or persistence.

## Database and development seed

```bash
cd apps/api
alembic upgrade head
cd ../..
SEED_ANALYST_PASSWORD='a-development-password' PYTHONPATH=apps/api python scripts/seed.py
```

The seed command refuses production mode and creates only a marked development identity and a policy; it does not fabricate telemetry.

## Detection and risk scoring

Each matched rule contributes a documented score. The strongest score plus 35% of additional signals is capped at 100. Severity bands are LOW 0-29, MEDIUM 30-59, HIGH 60-79, and CRITICAL 80-100. Correlated incidents retain the strongest event score and gain at most 10 points per subsequent event based on its matched signals. See [DETECTION.md](docs/DETECTION.md).

## ML

```bash
python -m ml.train
python -m ml.evaluate ml/model/baseline.joblib
```

Training writes a real joblib artifact and JSON report. The worker extracts aggregate event features, performs `predict_proba`, and persists the class, confidence, model version, and exact features. The supplied generator is synthetic and intentionally separable for pipeline verification only.

## API

- `POST /api/v1/ingest/events` — sensor-key protected ingestion.
- `/api/v1/auth/*` — registration, login, refresh, logout, password reset.
- `/api/v1/management/*` — protected events, incidents, attackers, sessions, alerts, intelligence, analytics, exports, administration, and SSE.
- `/health`, `/health/database`, `/health/redis`, `/health/workers`, `/health/honeypots` — live checks.

OpenAPI provides the exact request/response contracts in development.

## Verification

```bash
ruff check apps packages ml scripts
pytest
cd apps/web
npm audit
npm run lint
npm run typecheck
npm run build
```

Run explicit load telemetry (subject to the configured ingestion rate limit):

```bash
python scripts/generate_events.py --count 10000 --sensor-key "$SENSOR_API_KEY"
```

The script reports measured client throughput and latency; the repository makes no unmeasured throughput claims.

## Safe deployment

Place a TLS reverse proxy in front of the web management plane, restrict it by VPN/firewall, rotate all example secrets, keep API/PostgreSQL/Redis unexposed, configure retention/backups, and monitor resource usage. Bind management ports to loopback unless an authenticated proxy needs them. Treat captured credentials as sensitive data. This repository has been locally tested, but it has not undergone an independent penetration test and should not be exposed to the public internet without one.

An HTTPS overlay is included. After setting `TLS_CERT_PATH` and `TLS_KEY_PATH`, run `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`. It enables secure cookies and exposes only the TLS reverse proxy publicly; firewall the decoy and management ports according to your deployment.

## Documentation

- [Initial audit](docs/INITIAL_AUDIT.md)
- [Detection and scoring](docs/DETECTION.md)
- [Security model](docs/SECURITY.md)
- [Interview guide](docs/INTERVIEW_GUIDE.md)
- [Verification report](docs/VERIFICATION.md)

## Known limitations

- FTP, Telnet, and MySQL decoys are extension points, not implemented services.
- Email notification has an interface but only in-app and generic webhook delivery are implemented.
- GeoIP and reputation require a configured provider.
- Synthetic ML evaluation cannot establish real-world accuracy.
- Multi-instance API rate limiting depends on Redis; the local fallback is per process.
- Docker validation must be run on a host with Docker available.

## Resume description

**HoneyPot System — Full-Stack Cybersecurity Threat Detection Platform**

- Built a Next.js/FastAPI SOC platform backed by PostgreSQL, Redis Streams, Alembic, SSE, server-side analytics, and role-based incident workflows.
- Engineered isolated AsyncSSH and HTTP decoys that capture normalized telemetry without executing attacker input or exposing management-plane credentials.
- Implemented deterministic attack rules, transparent risk scoring, incident correlation, optional threat intelligence, webhook/in-app alerts, and an executable explainable ML baseline.
- Containerized seven services with non-root identities, read-only filesystems, dropped capabilities, segmented networks, health checks, and CI dependency/secret/container scanning.
