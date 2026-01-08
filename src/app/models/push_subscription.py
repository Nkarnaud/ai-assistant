from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscription"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String(255))
    auth_key: Mapped[str] = mapped_column(String(255))

    # Optional fields with defaults
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    device_name: Mapped[str | None] = mapped_column(String(255), default=None)

    # Fields with init=False
    is_active: Mapped[bool] = mapped_column(default=True, index=True, init=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
