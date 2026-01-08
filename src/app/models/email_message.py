from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class EmailClassification(str, Enum):
    """Classification types for emails."""

    CALENDAR_PLANNING = "calendar_planning"
    REQUIRES_REPLY = "requires_reply"
    INFORMATIONAL = "informational"
    SPAM = "spam"
    OTHER = "other"


class EmailMessage(Base):
    __tablename__ = "email_message"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first (no defaults)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    from_email: Mapped[str] = mapped_column(String(255), index=True)
    to_email: Mapped[str] = mapped_column(String(255))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Optional fields with defaults
    subject: Mapped[str] = mapped_column(String(500), default="")
    cc_emails: Mapped[str | None] = mapped_column(Text, default=None)
    bcc_emails: Mapped[str | None] = mapped_column(Text, default=None)
    body_text: Mapped[str | None] = mapped_column(Text, default=None)
    body_html: Mapped[str | None] = mapped_column(Text, default=None)
    snippet: Mapped[str | None] = mapped_column(String(500), default=None)
    classification: Mapped[str | None] = mapped_column(String(50), default=None)
    ai_analysis: Mapped[str | None] = mapped_column(Text, default=None)
    confidence_score: Mapped[float | None] = mapped_column(default=None)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Fields with init=False
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
