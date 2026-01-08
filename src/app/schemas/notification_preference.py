from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceBase(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    notify_15_min_before: bool = True
    notify_1_hour_before: bool = False
    notify_1_day_before: bool = False
    notify_new_draft: bool = True
    notify_calendar_event_created: bool = True
    notify_email_classified: bool = False
    auto_approve_high_confidence: bool = False
    confidence_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.95


class NotificationPreference(NotificationPreferenceBase):
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None


class NotificationPreferenceRead(BaseModel):
    id: int
    user_id: int
    email_notifications: bool
    push_notifications: bool
    notify_15_min_before: bool
    notify_1_hour_before: bool
    notify_1_day_before: bool
    notify_new_draft: bool
    notify_calendar_event_created: bool
    notify_email_classified: bool
    auto_approve_high_confidence: bool
    confidence_threshold: float
    created_at: datetime


class NotificationPreferenceCreate(NotificationPreferenceBase):
    model_config = ConfigDict(extra="forbid")


class NotificationPreferenceCreateInternal(NotificationPreferenceBase):
    user_id: int


class NotificationPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_notifications: bool | None = None
    push_notifications: bool | None = None
    notify_15_min_before: bool | None = None
    notify_1_hour_before: bool | None = None
    notify_1_day_before: bool | None = None
    notify_new_draft: bool | None = None
    notify_calendar_event_created: bool | None = None
    notify_email_classified: bool | None = None
    auto_approve_high_confidence: bool | None = None
    confidence_threshold: Annotated[float | None, Field(ge=0.0, le=1.0)] = None


class NotificationPreferenceUpdateInternal(NotificationPreferenceUpdate):
    updated_at: datetime
