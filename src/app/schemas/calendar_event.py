from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CalendarEventBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=500, examples=["Team Meeting"])]
    description: str | None = None
    location: Annotated[str | None, Field(max_length=500)] = None
    start_time: datetime
    end_time: datetime
    timezone: Annotated[str, Field(max_length=50)] = "UTC"
    attendees: str | None = None  # JSON string of email list


class CalendarEvent(CalendarEventBase):
    user_id: int
    email_message_id: int | None = None
    google_event_id: str
    calendar_id: str = "primary"
    is_all_day: bool = False
    created_from_email: bool = False
    auto_created: bool = False
    confidence_score: float | None = None
    notification_sent: bool = False
    notification_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    synced_at: datetime | None = None


class CalendarEventRead(BaseModel):
    id: int
    user_id: int
    email_message_id: int | None
    google_event_id: str
    calendar_id: str
    title: str
    description: str | None
    location: str | None
    start_time: datetime
    end_time: datetime
    timezone: str
    is_all_day: bool
    created_from_email: bool
    auto_created: bool
    confidence_score: float | None
    created_at: datetime


class CalendarEventWithEmail(CalendarEventRead):
    """Calendar event with associated email details if created from email."""

    email_subject: str | None
    email_from: str | None


class CalendarEventCreate(CalendarEventBase):
    model_config = ConfigDict(extra="forbid")

    calendar_id: str = "primary"


class CalendarEventCreateInternal(CalendarEventBase):
    user_id: int
    email_message_id: int | None
    google_event_id: str
    calendar_id: str = "primary"
    created_from_email: bool = False
    auto_created: bool = False
    confidence_score: float | None = None


class CalendarEventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(min_length=1, max_length=500)] = None
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None


class CalendarEventUpdateInternal(CalendarEventUpdate):
    updated_at: datetime
    synced_at: datetime | None = None


class CalendarEventExtracted(BaseModel):
    """Extracted calendar event data from email (before creation)."""

    title: str
    description: str | None = None
    location: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    attendees: list[str] = []
    confidence_score: float
    extraction_reasoning: str
