# Security model

## Trust boundaries

- SSH and HTTP decoys are untrusted, internet-facing workloads. They only know an ingestion URL and sensor key.
- The API is the gateway between the sensor and management networks.
- PostgreSQL, Redis, worker, and web management plane are on an internal management network. Decoys cannot connect to them directly.
- Analysts authenticate through the Next.js backend-for-frontend; tokens are stored in HTTP-only cookies.

## Controls

- Containers use non-root users, `cap_drop: ALL`, `no-new-privileges`, PID/CPU/memory limits, and read-only root filesystems where possible.
- The virtual SSH shell maps commands to static responses and has no subprocess or filesystem execution path.
- HTTP responses are fixed decoys; authorization/cookie headers are redacted before storage and bodies are size-limited.
- Sensor keys use constant-time comparison. Management uses short-lived signed access tokens, rotating hashed refresh tokens, Argon2 passwords, and RBAC.
- Password-reset and refresh tokens are stored only as SHA-256 digests. Reset delivery is disabled unless a private webhook is configured.
- Ingestion has Content-Length enforcement and Redis rate limiting, with a per-process fallback during Redis failure.
- Captured passwords are never stored directly: only an HMAC fingerprint is persisted. Logs exclude secrets.
- Management mutations and exports write audit records.

## Assumptions and limitations

The sensor key is shared by current decoys; a production fleet should use per-node credentials and rotation. The generic threat-intelligence and reset webhooks must themselves be trusted and TLS-protected. Docker isolation reduces impact but is not a substitute for host patching, firewalling, monitoring, and an independent penetration test. Management access should remain behind a VPN or identity-aware proxy.
