"""Seed development-only identities and default alert policy."""
import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import AlertRule, Role, RoleName, User


def main() -> None:
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise SystemExit("Refusing to seed development identities in production")
    email = os.getenv("SEED_ANALYST_EMAIL", "analyst@example.test").lower()
    password = os.getenv("SEED_ANALYST_PASSWORD")
    if not password or len(password) < 12:
        raise SystemExit("Set SEED_ANALYST_PASSWORD to at least 12 characters")
    with SessionLocal() as db:
        role = db.scalar(select(Role).where(Role.name == RoleName.ANALYST))
        if role is None:
            raise SystemExit("Run Alembic migrations first")
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(User(email=email, password_hash=hash_password(password), role_id=role.id))
        if db.scalar(select(AlertRule).where(AlertRule.name == "Critical incidents")) is None:
            db.add(AlertRule(name="Critical incidents", minimum_score=80, channels=["IN_APP", "WEBHOOK"]))
        db.commit()
    print("Development seed complete; no telemetry was fabricated.")


if __name__ == "__main__":
    main()
