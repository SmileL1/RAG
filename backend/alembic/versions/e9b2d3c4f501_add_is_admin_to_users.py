"""add is_admin to users

Revision ID: e9b2d3c4f501
Revises: c3f8a12e9d45
Create Date: 2026-04-29 12:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e9b2d3c4f501"
down_revision: str | None = "c3f8a12e9d45"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # 把 username='admin' 的账号设为管理员
    op.execute("UPDATE users SET is_admin = TRUE WHERE username = 'admin'")


def downgrade() -> None:
    op.drop_column("users", "is_admin")
