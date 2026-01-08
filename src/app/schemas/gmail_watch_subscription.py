from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GmailWatchSubscriptionBase(BaseModel):
    history_id: int
    expiration: datetime
    topic_name: Annotated[str, Field(max_length=255)]
    subscription_name: Annotated[str | None, Field(max_length=255)] = None


class GmailWatchSubscription(GmailWatchSubscriptionBase):
    user_id: int
    is_active: bool = True
    last_renewed_at: datetime | None = None
    renewal_failures: int = 0
    created_at: datetime
    updated_at: datetime | None = None


class GmailWatchSubscriptionRead(BaseModel):
    id: int
    user_id: int
    history_id: int
    expiration: datetime
    topic_name: str
    subscription_name: str | None
    is_active: bool
    last_renewed_at: datetime | None
    renewal_failures: int
    created_at: datetime


class GmailWatchSubscriptionCreate(GmailWatchSubscriptionBase):
    model_config = ConfigDict(extra="forbid")


class GmailWatchSubscriptionCreateInternal(GmailWatchSubscriptionBase):
    user_id: int


class GmailWatchSubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    history_id: int | None = None
    expiration: datetime | None = None
    is_active: bool | None = None
    last_renewed_at: datetime | None = None
    renewal_failures: int | None = None


class GmailWatchSubscriptionUpdateInternal(GmailWatchSubscriptionUpdate):
    updated_at: datetime
