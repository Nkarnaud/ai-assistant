from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class EmailMessageBase(BaseModel):
    subject: Annotated[str, Field(max_length=500, examples=["Meeting tomorrow at 3pm"])] = ""
    from_email: Annotated[str, Field(max_length=255, examples=["sender@example.com"])]
    to_email: Annotated[str, Field(max_length=255, examples=["recipient@example.com"])]
    cc_emails: str | None = None
    bcc_emails: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    snippet: Annotated[str | None, Field(max_length=500)] = None
    received_at: datetime


class EmailMessage(EmailMessageBase):
    user_id: int
    message_id: str
    thread_id: str
    classification: str | None = None
    ai_analysis: str | None = None
    confidence_score: float | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class EmailMessageRead(BaseModel):
    id: int
    user_id: int
    message_id: str
    thread_id: str
    subject: str
    from_email: str
    to_email: str
    snippet: str | None
    classification: str | None
    confidence_score: float | None
    received_at: datetime
    processed_at: datetime | None
    created_at: datetime


class EmailMessageCreate(EmailMessageBase):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    thread_id: str


class EmailMessageCreateInternal(EmailMessageCreate):
    user_id: int


class EmailMessageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: str | None = None
    ai_analysis: str | None = None
    confidence_score: float | None = None
    processed_at: datetime | None = None


class EmailMessageUpdateInternal(EmailMessageUpdate):
    updated_at: datetime


class EmailMessageWithDraft(EmailMessageRead):
    """Email message with associated draft reply if exists."""

    has_draft: bool = False
    draft_id: int | None = None
    draft_status: str | None = None
