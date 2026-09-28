# Interview guide

## Why PostgreSQL?

Telemetry and investigations need durable transactions, joins, indexes, constraints, and server-side aggregation. PostgreSQL is authoritative; Redis is never the system of record.

## Why Redis and an asynchronous worker?

Redis Streams decouples slow enrichment, ML inference, and notification delivery from ingestion latency. Consumer groups support multiple workers. If Redis fails, ingestion still commits events; health turns unhealthy and missed jobs can be replayed by a future reconciliation process.

## Why SSE?

The dashboard needs server-to-client telemetry, not bidirectional messaging. SSE works over ordinary HTTP, reconnects naturally, and is simpler to operate through proxies than a WebSocket for this one-way flow.

## How is the honeypot safe?

The AsyncSSH server accepts the decoy login but routes every line to `VirtualShell`, a pure mapping of commands to simulated strings. It never calls a shell, subprocess, `eval`, or the host filesystem. Docker adds a non-root identity, dropped capabilities, a read-only root, resource limits, and network segmentation.

## How do detection, scoring, and correlation work?

Every event is normalized first. Rules inspect the event plus real 60-second database context. Matched signals contribute documented points capped at 100 and map to four severity bands. Detected events from the same IP join an unresolved incident within 15 minutes, accumulating attack types and bounded score increases. The formula is in `docs/DETECTION.md`.

## How is ML integrated?

The worker extracts eight aggregate incident features and loads a versioned logistic-regression pipeline. It persists class, `predict_proba` confidence, model version, and input features. The bundled dataset is synthetic development data and the UI must not present its evaluation as production efficacy. Rules remain primary.

## What happens when dependencies fail?

- PostgreSQL failure: ingestion cannot safely persist and the database health check fails; the API does not pretend success.
- Redis failure: synchronous persistence/detection continues and a local rate-limit fallback activates, but background work and live pub/sub degrade.
- Threat provider failure: bounded retries record `ERROR`; existing telemetry remains usable.
- AI failure or missing key: only the optional analyst endpoint returns unavailable; detection is unaffected.

## How is the management plane protected?

Only the API bridges networks. Decoys receive no DB/Redis credentials. Browser requests pass through a Next.js BFF using HTTP-only tokens. FastAPI enforces authentication on the management router and ADMIN/ANALYST checks on mutations and exports. Production management ports bind to loopback and should sit behind TLS/VPN.

## How would this scale to 10,000 events/minute?

Run multiple stateless API and worker replicas, use per-node sensor credentials, batch ingestion, partition events by time, add a durable queue if replay guarantees require it, pre-aggregate dashboard windows, and move SSE fan-out to Redis pub/sub. Benchmark each change before stating throughput.

## How would millions of events be stored?

Use monthly/daily PostgreSQL partitions, retention tiers, compressed object storage for old payloads, rollup tables, and targeted indexes. Current indexes cover timestamps, source IP plus timestamp, event type, session, severity, incident status, and common foreign keys.

## Why these indexes?

Investigation starts from source IP, session, time, type, severity, or status. Composite `source_ip,timestamp` and `timestamp,event_type` indexes match the hottest ordered filters; foreign-key indexes keep joins predictable.

## Authentication details

Passwords use Argon2. Access JWTs expire quickly. Opaque refresh tokens are random, stored as hashes, rotated on use, and revoked on logout/reset. Reset tokens are one-time and expiring. Roles are ADMIN, ANALYST, and VIEWER.

## Honest security assumptions

This is a controlled decoy, not a malware sandbox. It does not execute samples. A compromised container runtime or leaked sensor key remains in scope for host operations, rotation, firewall policy, and monitoring. Public deployment requires independent review.
