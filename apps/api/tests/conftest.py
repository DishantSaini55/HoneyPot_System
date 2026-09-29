import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test-honeypot.db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6399/15")
os.environ.setdefault("JWT_SECRET", "test-only-secret-that-is-at-least-32-characters-long")
os.environ.setdefault("SENSOR_API_KEY", "test-sensor-key-at-least-24-characters")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.entities import Role, RoleName
from app.services.rate_limit import clear_fallback


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    clear_fallback()
    yield
    clear_fallback()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add_all(
            [
                Role(name=RoleName.ADMIN, description="Admin"),
                Role(name=RoleName.ANALYST, description="Analyst"),
                Role(name=RoleName.VIEWER, description="Viewer"),
            ]
        )
        db.commit()
        yield db
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
