"""add password_hash to users

Revision ID: 0002_password_hash
Revises: 56d7b70d05dd
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_password_hash"
down_revision: Union[str, None] = "56d7b70d05dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=128), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
