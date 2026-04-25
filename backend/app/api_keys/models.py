"""User API key database models."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class UserApiKey(Base):
    """
    API key for MCP and external integrations.

    Attributes:
        id: Primary key.
        user_id: Foreign key to the users table.
        name: User-provided label for the key.
        key_prefix: First 8 chars of the raw key
            (for display).
        key_hash: SHA-256 hex digest of the raw key.
        created_at: When the key was created (UTC).
        last_used_at: When the key was last used.
        expires_at: Optional expiration timestamp.
        users: Many-to-one relationship with Users.
    """

    __tablename__ = "user_api_keys"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this API key",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User-provided label for the key",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="First 8 chars of raw key for display",
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hex digest of the raw key",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When the key was created",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When the key was last used",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Optional expiration timestamp",
    )

    users = relationship(
        "Users",
        back_populates="api_keys",
    )

    __table_args__ = (
        Index(
            "idx_user_api_keys_user_id_name",
            "user_id",
            "name",
        ),
    )
