from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class GmailWatchSubscription(Base):
    __tablename__ = "gmail_watch_subscription"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)

    # Required fields first
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    history_id: Mapped[int] = mapped_column(BigInteger)
    expiration: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    topic_name: Mapped[str] = mapped_column(String(255))

    # Optional fields with defaults
    subscription_name: Mapped[str | None] = mapped_column(String(255), default=None)

    # Fields with init=False
    is_active: Mapped[bool] = mapped_column(default=True, index=True, init=False)
    last_renewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    renewal_failures: Mapped[int] = mapped_column(Integer, default=0, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
