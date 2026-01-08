from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DraftReplyBase(BaseModel):
    draft_content: Annotated[str, Field(min_length=1, examples=["Thank you for your email..."])]
    ai_model_used: Annotated[str, Field(max_length=100, examples=["claude-3-5-sonnet-20241022"])]
    confidence_score: Annotated[float, Field(ge=0.0, le=1.0)]
    analysis_context: str | None = None


class DraftReply(DraftReplyBase):
    email_message_id: int
    user_id: int
    status: str
    reviewed_at: datetime | None = None
    sent_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DraftReplyRead(BaseModel):
    id: int
    email_message_id: int
    user_id: int
    draft_content: str
    ai_model_used: str
    confidence_score: float
    analysis_context: str | None
    status: str
    reviewed_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class DraftReplyWithEmail(DraftReplyRead):
    """Draft reply with associated email details."""

    email_subject: str
    email_from: str
    email_received_at: datetime
    email_snippet: str | None


class DraftReplyCreate(DraftReplyBase):
    model_config = ConfigDict(extra="forbid")


class DraftReplyCreateInternal(DraftReplyBase):
    email_message_id: int
    user_id: int
    original_draft: str


class DraftReplyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_content: str | None = None
    status: str | None = None
    reviewed_at: datetime | None = None
    sent_at: datetime | None = None
    rejection_reason: str | None = None


class DraftReplyUpdateInternal(DraftReplyUpdate):
    updated_at: datetime


class DraftReplyApprove(BaseModel):
    """Schema for approving a draft (optionally with edits)."""

    model_config = ConfigDict(extra="forbid")

    edited_content: str | None = None


class DraftReplyReject(BaseModel):
    """Schema for rejecting a draft."""

    model_config = ConfigDict(extra="forbid")

    rejection_reason: Annotated[str | None, Field(max_length=500)] = None
