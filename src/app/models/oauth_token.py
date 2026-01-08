from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class OAuthToken(Base):
    __tablename__ = "oauth_token"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)

    access_token: Mapped[str] = mapped_column(Text, init=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, default=None, init=False)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer", init=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), init=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default_factory=list, init=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
