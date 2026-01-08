from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preference"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)

    # Optional fields with defaults
    email_notifications: Mapped[bool] = mapped_column(default=True)
    push_notifications: Mapped[bool] = mapped_column(default=True)
    notify_15_min_before: Mapped[bool] = mapped_column(default=True)
    notify_1_hour_before: Mapped[bool] = mapped_column(default=False)
    notify_1_day_before: Mapped[bool] = mapped_column(default=False)
    notify_new_draft: Mapped[bool] = mapped_column(default=True)
    notify_calendar_event_created: Mapped[bool] = mapped_column(default=True)
    notify_email_classified: Mapped[bool] = mapped_column(default=False)
    auto_approve_high_confidence: Mapped[bool] = mapped_column(default=False)
    confidence_threshold: Mapped[float] = mapped_column(default=0.95)

    # Fields with init=False
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
