# Initial Repository Audit

Audit date: 2026-09-29  
Audited commit: `84302976674a661f487ded6365776863d0ab040c`

## Existing architecture

The repository is a Vite/React single-page application with a small Flask API and
an AsyncSSH-based decoy service.

The implemented runtime path is:

```text
SSH client -> AsyncSSH listener -> optional Featherless LLM response
           -> unauthenticated Flask telemetry endpoint -> process-memory list
           -> React polling
```

Most dashboard views do not use that path. They read static arrays from
`src/data/mockData.js`. The map, attacker profiles, risk scores, classifications,
swarm nodes, attack timelines, session export, and alert count are therefore demo
content rather than observed telemetry.

### Frontend

- React 18, Vite, JavaScript, Tailwind CSS, React Router, Leaflet.
- `/dashboard`, `/telemetry`, and `/intel` client routes.
- Polls `/api/telemetry/logs` for the narrow SSH telemetry feed.
- Uses mock attackers and sessions for the primary dashboard and exports.
- Contains an unused `AttackDVR` component and a placeholder node graph.
- Deletes server telemetry when the Node-AI telemetry view is opened.

### Backend

- One `backend/app.py` Flask module.
- Health, AI completion, AI chat, and in-memory telemetry CRUD endpoints.
- No authentication, authorization, schema validation, database, migrations,
  correlation, detection, alerts, analytics, pagination, or audit log.
- Debug mode is hardcoded on and the server binds to `0.0.0.0:5000`.

### SSH service

- AsyncSSH listener hardcoded to `0.0.0.0:2222`.
- Accepts every password and writes captured credentials to the normal console.
- Captures commands and posts them to Flask.
- Never executes the supplied command on the host, which is useful and will be
  retained as a security invariant.
- Requires `asyncssh` and `aiohttp`, neither of which is declared.
- Without an LLM key it records a fallback error but sends a blank response to
  the SSH client. HTTP responses are not consumed correctly, causing connection
  leakage. Session termination is unreliable.

### ML prototype

`prototype_ml_classification.py` explicitly describes itself as pseudo-code. It
references undefined functions and nonexistent model artifacts. It is not
imported by the running application.

## Problems discovered

### Functional

1. A fresh install cannot import or start the SSH service.
2. `openai==1.51.2` resolves with incompatible `httpx==0.28.1`; configuring an
   API key crashes both synchronous and asynchronous OpenAI clients.
3. Telemetry disappears whenever Flask restarts.
4. There is no attack detection or correlation pipeline.
5. HTTP, FTP, MySQL, alerting, threat intelligence, analytics, and ML features
   displayed or described by the project are not implemented.
6. AI chat does not receive stored incident data.
7. Dashboard exports contain hardcoded sessions.
8. The documented port environment variables are ignored.
9. The CARTO map source currently renders an API-key-required response.

### Security

1. Any network client can read, forge, update, or delete telemetry.
2. Flask's debugger is exposed on all interfaces.
3. Attacker-facing and management services have no network boundary.
4. There are no request limits, rate limits, session limits, or retention limits.
5. Captured passwords are logged without a sensitive-data policy.
6. Attacker commands may be sent to an external LLM without redaction.
7. There is no container/VM isolation, non-root runtime, read-only filesystem,
   capability drop, or outbound policy.
8. The frontend dependency audit reports high-severity advisories.

### Documentation and delivery

- No `.env.example`, Docker configuration, migrations, CI, automated tests,
  production server, operational runbook, or real license file.
- README claims exceed the implementation.
- There is no evidence for accuracy, throughput, uptime, or detection-rate claims.

## Useful code to reuse

- The existing visual direction and some Tailwind styling concepts.
- The safe invariant that SSH commands are interpreted by a simulator and never
  passed to a host shell.
- The basic AsyncSSH server lifecycle, after rewriting session handling,
  dependency management, and ingestion.
- The idea of a provider-compatible optional AI enhancement, moved behind a safe
  interface with deterministic responses as the default.

## Code to rewrite or retire

- Replace Flask with modular FastAPI.
- Replace process-memory telemetry with PostgreSQL models and Alembic migrations.
- Replace public telemetry mutation with sensor-key ingestion and JWT-protected
  management APIs.
- Rewrite the SSH service around a deterministic virtual shell.
- Add a separate HTTP honeypot service.
- Replace mock dashboard data with authenticated API queries and SSE updates.
- Replace pseudo-ML with an executable, explicitly development-grade baseline.
- Retire the current mock data, fake export, placeholder graph, destructive log
  clearing, and false database archival messages.

## Migration strategy

1. Establish the monorepo structure and configuration contract.
2. Add the FastAPI domain model, PostgreSQL persistence, authentication, RBAC,
   consistent event ingestion, and Alembic.
3. Add deterministic rules, transparent risk scoring, incident correlation,
   in-app alerts, audit logging, analytics, filtering, and export.
4. Rewrite SSH and implement HTTP sensors. Sensors authenticate only to an
   ingestion endpoint and receive no database or management credentials.
5. Add Redis Streams for durable background work and SSE for live management
   updates, with database-backed fallback behavior.
6. Migrate the web application to Next.js/TypeScript and remove production mock
   data.
7. Add optional threat-intelligence and AI adapters which fail closed and never
   block core detection.
8. Add an executable baseline ML workflow whose synthetic development dataset is
   clearly labeled and whose measured metrics are generated by the evaluator.
9. Add rootless, restricted containers, separated networks, health checks, CI,
   tests, and truthful operational documentation.

## Validation baseline

The pre-migration audit verified that the React production bundle builds and the
Flask health endpoint responds. It also verified that an SSH interaction can be
captured only after undeclared packages are installed. HTTP probes, SQL injection,
path traversal, command injection, suspicious user agents, and repeated requests
were not detected or stored. These observations are the regression baseline for
the replacement system.
