"""Create the initial HoneyPot schema.

Revision ID: 0001
Revises:
"""
from alembic import op
from sqlalchemy import insert

from app.core.database import Base
from app.models.entities import Role, RoleName
from app import models  # noqa: F401


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    bind.execute(
        insert(Role),
        [
            {"name": RoleName.ADMIN, "description": "Full administrative access"},
            {"name": RoleName.ANALYST, "description": "Investigate and manage incidents"},
            {"name": RoleName.VIEWER, "description": "Read-only dashboard access"},
        ],
    )


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

