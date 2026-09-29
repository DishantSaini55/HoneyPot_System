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

## Native Windows quick start (Docker not required)

Prerequisites: Windows 10/11, Python 3.12, Node.js 20+ (validated with Node 22), npm 10+, and PowerShell. The setup script uses a repository-local actual PostgreSQL distribution and native Redis 8 for Windows; it does not install Docker or require administrator-installed PostgreSQL.

```powershell
# One-time native Redis installation (Redis 8 Windows fork)
winget install --id taizod1024.redis-windows-fork --source winget

py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt -r ml/requirements.txt
.venv\Scripts\python -m pip install -e packages/sensor-sdk -r apps/ssh-honeypot/requirements.txt -r apps/http-honeypot/requirements.txt
Push-Location apps/web; npm.cmd ci; Pop-Location

# Creates ignored .runtime/native.env with random local-only secrets, initializes PostgreSQL, and starts PostgreSQL + Redis.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-infra.ps1 setup

# Train the local development-only model, build Next.js, migrate, and start API, worker, SSH/HTTP decoys, and web.
.venv\Scripts\python -m ml.train
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-stack.ps1 start
```

The native services bind to loopback by default: web `http://127.0.0.1:3000`, API `http://127.0.0.1:8000`, HTTP decoy `http://127.0.0.1:8080`, SSH decoy `127.0.0.1:2222`, PostgreSQL `127.0.0.1:55432`, and Redis `127.0.0.1:56379`. Open the web URL, register the exact `BOOTSTRAP_ADMIN_EMAIL` from `.runtime/native.env`, and the first matching account becomes ADMIN. API docs are available in development at `http://127.0.0.1:8000/docs`.

Use `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-stack.ps1 status` for state, and replace `start` with `stop` to stop the application stack and local data services. Runtime data, logs, generated secrets, and the PostgreSQL cluster live in ignored `.runtime/`.

Exercise the decoys:

```bash
ssh -p 2222 admin@localhost
curl http://localhost:8080/admin
curl http://localhost:8080/.env
curl "http://localhost:8080/..%2f..%2fetc/passwd"
```

## Optional containerized deployment

Docker is retained for deployment only; it is not a local development or validation prerequisite. After creating a production `.env` with unique secrets, use `docker compose up --build`. For the TLS overlay, set `TLS_CERT_PATH` and `TLS_KEY_PATH` and use `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`.

## Native development commands

The managed native path above is recommended. For individual processes, first load the generated environment in each PowerShell session:

```powershell
Get-Content .runtime\native.env | ForEach-Object { if ($_ -and -not $_.StartsWith('#')) { $n, $v = $_.Split('=', 2); Set-Item "Env:$n" $v } }
$env:PYTHONPATH = "apps/api;packages/sensor-sdk;."
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv\Scripts\python apps/worker/main.py
.venv\Scripts\python apps/ssh-honeypot/main.py
.venv\Scripts\python -m uvicorn main:app --app-dir apps/http-honeypot --host 127.0.0.1 --port 8080
```

For the frontend development server, use `Push-Location apps/web; $env:API_URL = 'http://127.0.0.1:8000'; npm.cmd run dev; Pop-Location`. The tracked `native-stack.ps1` launcher uses the supported Next standalone production server and copies its static assets.

## Configuration

All variables are documented in [.env.example](.env.example). Required production values are `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, and `SENSOR_API_KEY`. Ports, token lifetimes, CORS, body/rate limits, threat-intel provider, webhook alerting, optional AI, model path, and logging are configurable. `.env` files are ignored by Git.

External intelligence, webhook, password-reset delivery, and AI calls are disabled unless their URLs/keys are configured. Their absence never disables deterministic detection or persistence.

## Database and development seed

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-infra.ps1 start
Push-Location apps/api; ..\..\.venv\Scripts\python -m alembic upgrade head; Pop-Location
$env:SEED_ANALYST_PASSWORD='a-development-password'; $env:PYTHONPATH='apps/api'; .venv\Scripts\python scripts/seed.py
```

The seed command refuses production mode and creates only a marked development identity and a policy; it does not fabricate telemetry.

## Detection and risk scoring

Each matched rule contributes a documented score. The strongest score plus 35% of additional signals is capped at 100. Severity bands are LOW 0-29, MEDIUM 30-59, HIGH 60-79, and CRITICAL 80-100. Correlated incidents retain the strongest event score and gain at most 10 points per subsequent event based on its matched signals. See [DETECTION.md](docs/DETECTION.md).

## ML

```powershell
.venv\Scripts\python -m ml.train
.venv\Scripts\python -m ml.evaluate ml/model/baseline.joblib
```

Training writes a real joblib artifact and JSON report. The worker extracts aggregate event features, performs `predict_proba`, and persists the class, confidence, model version, and exact features. The supplied generator is synthetic and intentionally separable for pipeline verification only.

## API

- `POST /api/v1/ingest/events` — sensor-key protected ingestion.
- `/api/v1/auth/*` — registration, login, refresh, logout, password reset.
- `/api/v1/management/*` — protected events, incidents, attackers, sessions, alerts, intelligence, analytics, exports, administration, and SSE.
- `/health`, `/health/database`, `/health/redis`, `/health/workers`, `/health/honeypots` — live checks.

OpenAPI provides the exact request/response contracts in development.

## Verification

```powershell
.venv\Scripts\python -m ruff check apps packages ml scripts
.venv\Scripts\python -m pytest
Push-Location apps/web
npm.cmd audit
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
Pop-Location
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/native-stack.ps1 start
# In a second shell with .runtime/native.env loaded:
.venv\Scripts\python scripts/validate_honeypots.py
.venv\Scripts\python scripts/validate_detection_pipeline.py
.venv\Scripts\python scripts/validate_auth_runtime.py
```

Run explicit load telemetry (subject to the configured ingestion rate limit):

```powershell
.venv\Scripts\python scripts/generate_events.py --count 10000 --sensor-key $env:SENSOR_API_KEY
```

The script reports measured client throughput and latency; the repository makes no unmeasured throughput claims.

## Safe deployment

Place a TLS reverse proxy in front of the web management plane, restrict it by VPN/firewall, rotate all example secrets, keep API/PostgreSQL/Redis unexposed, configure retention/backups, and monitor resource usage. Bind management ports to loopback unless an authenticated proxy needs them. Treat captured credentials as sensitive data. This repository has been locally tested, but it has not undergone an independent penetration test and should not be exposed to the public internet without one.

An HTTPS overlay is included for optional containerized deployment. It enables secure cookies and exposes only the TLS reverse proxy publicly; firewall the decoy and management ports according to your deployment.

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
- Container deployment validation requires a host with Docker available; native development and validation do not.

## Resume description

**HoneyPot System — Full-Stack Cybersecurity Threat Detection Platform**

- Built a Next.js/FastAPI SOC platform backed by PostgreSQL, Redis Streams, Alembic, SSE, server-side analytics, and role-based incident workflows.
- Engineered isolated AsyncSSH and HTTP decoys that capture normalized telemetry without executing attacker input or exposing management-plane credentials.
- Implemented deterministic attack rules, transparent risk scoring, incident correlation, optional threat intelligence, webhook/in-app alerts, and an executable explainable ML baseline.
- Containerized seven services with non-root identities, read-only filesystems, dropped capabilities, segmented networks, health checks, and CI dependency/secret/container scanning.
