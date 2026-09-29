"""Redis-backed fixed-window limits with a small process-local availability fallback."""

from collections import defaultdict, deque
from hashlib import sha256
from time import monotonic

from redis import Redis

from app.core.config import get_settings


_fallback: dict[str, deque[float]] = defaultdict(deque)


def _key(action: str, source_ip: str, subject: str) -> str:
    # Do not expose email addresses in Redis keys.
    identity = sha256(f"{source_ip}|{subject.strip().lower()}".encode("utf-8")).hexdigest()
    return f"honeypot:rate:auth:{action}:{identity}"


def is_allowed(action: str, source_ip: str, subject: str, limit: int) -> bool:
    """Return whether an action is inside its configured limit.

    Redis is the shared source of truth. The fallback preserves basic protection
    during a Redis outage, while the health endpoint makes that outage visible.
    """
    settings = get_settings()
    window = settings.auth_rate_limit_window_seconds
    key = _key(action, source_ip, subject)
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25)
        count = client.incr(key)
        if count == 1:
            client.expire(key, window)
        client.close()
        return count <= limit
    except Exception:
        now = monotonic()
        bucket = _fallback[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        bucket.append(now)
        return len(bucket) <= limit


def clear_fallback() -> None:
    """Test helper; production code never needs to clear rate-limit state."""
    _fallback.clear()
