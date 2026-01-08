from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_event"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first (no defaults)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    google_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Optional fields with defaults
    email_message_id: Mapped[int | None] = mapped_column(ForeignKey("email_message.id"), default=None, index=True)
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    location: Mapped[str | None] = mapped_column(String(500), default=None)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    attendees: Mapped[str | None] = mapped_column(Text, default=None)

    # Fields with init=False (not in constructor)
    is_all_day: Mapped[bool] = mapped_column(default=False, init=False)
    created_from_email: Mapped[bool] = mapped_column(default=False, index=True, init=False)
    auto_created: Mapped[bool] = mapped_column(default=False, init=False)
    confidence_score: Mapped[float | None] = mapped_column(default=None, init=False)
    notification_sent: Mapped[bool] = mapped_column(default=False, init=False)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
