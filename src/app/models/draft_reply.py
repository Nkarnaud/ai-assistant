from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class DraftStatus(str, Enum):
    """Status of draft replies."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class DraftReply(Base):
    __tablename__ = "draft_reply"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first (no defaults)
    email_message_id: Mapped[int] = mapped_column(ForeignKey("email_message.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    draft_content: Mapped[str] = mapped_column(Text)
    ai_model_used: Mapped[str] = mapped_column(String(100))
    confidence_score: Mapped[float] = mapped_column(Float)

    # Optional fields with defaults
    analysis_context: Mapped[str | None] = mapped_column(Text, default=None)

    # Fields with init=False (not in constructor)
    original_draft: Mapped[str] = mapped_column(Text, init=False)  # Store original before edits
    status: Mapped[str] = mapped_column(String(20), default=DraftStatus.PENDING.value, index=True, init=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, default=None, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
