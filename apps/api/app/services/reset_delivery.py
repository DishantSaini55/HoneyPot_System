"""Signed password-reset webhook delivery."""

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings


def build_signed_reset_delivery(email: str, reset_token: str) -> tuple[dict, dict[str, str]]:
    settings = get_settings()
    secret = settings.password_reset_webhook_secret
    if not secret:
        raise RuntimeError("PASSWORD_RESET_WEBHOOK_SECRET is required when webhook delivery is enabled")
    timestamp = str(int(datetime.now(UTC).timestamp()))
    payload = {
        "event": "password_reset",
        "delivery_id": str(uuid.uuid4()),
        "email": email,
        "reset_token": reset_token,
        "issued_at": datetime.now(UTC).isoformat(),
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        secret.get_secret_value().encode("utf-8"),
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return payload, {
        "Content-Type": "application/json",
        "X-Honeypot-Timestamp": timestamp,
        "X-Honeypot-Signature": f"sha256={signature}",
        "X-Honeypot-Delivery-Id": payload["delivery_id"],
    }


def deliver_password_reset(email: str, reset_token: str) -> None:
    settings = get_settings()
    if not settings.password_reset_webhook_url:
        return
    payload, headers = build_signed_reset_delivery(email, reset_token)
    httpx.post(settings.password_reset_webhook_url, json=payload, headers=headers, timeout=3.0).raise_for_status()
