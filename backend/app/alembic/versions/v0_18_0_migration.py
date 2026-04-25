"""v0.18.0 migration

Revision ID: 7b78b0e5f1f0
Revises: 262ec21a6c15
Create Date: 2026-04-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7b78b0e5f1f0"
down_revision: Union[str, None] = "262ec21a6c15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_api_keys",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
            comment="User who owns this API key",
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="User-provided label for the key",
        ),
        sa.Column(
            "key_prefix",
            sa.String(length=8),
            nullable=False,
            comment="First 8 chars of raw key for display",
        ),
        sa.Column(
            "key_hash",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 hex digest of the raw key",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="When the key was created",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(),
            nullable=True,
            comment="When the key was last used",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=True,
            comment="Optional expiration timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_api_keys_user_id"),
        "user_api_keys",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_api_keys_key_hash"),
        "user_api_keys",
        ["key_hash"],
        unique=True,
    )
    op.create_index(
        "idx_user_api_keys_user_id_name",
        "user_api_keys",
        ["user_id", "name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_user_api_keys_user_id_name",
        table_name="user_api_keys",
    )
    op.drop_index(
        op.f("ix_user_api_keys_key_hash"),
        table_name="user_api_keys",
    )
    op.drop_index(
        op.f("ix_user_api_keys_user_id"),
        table_name="user_api_keys",
    )
    op.drop_table("user_api_keys")
