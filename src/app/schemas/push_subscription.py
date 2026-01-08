from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PushSubscriptionBase(BaseModel):
    endpoint: str
    p256dh_key: Annotated[str, Field(max_length=255)]
    auth_key: Annotated[str, Field(max_length=255)]
    user_agent: str | None = None
    device_name: Annotated[str | None, Field(max_length=255)] = None


class PushSubscription(PushSubscriptionBase):
    user_id: int
    is_active: bool = True
    last_used_at: datetime | None = None
    failure_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None


class PushSubscriptionRead(BaseModel):
    id: int
    user_id: int
    endpoint: str
    device_name: str | None
    is_active: bool
    last_used_at: datetime | None
    failure_count: int
    created_at: datetime


class PushSubscriptionCreate(PushSubscriptionBase):
    model_config = ConfigDict(extra="forbid")


class PushSubscriptionCreateInternal(PushSubscriptionBase):
    user_id: int


class PushSubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool | None = None
    last_used_at: datetime | None = None
    failure_count: int | None = None


class PushSubscriptionUpdateInternal(PushSubscriptionUpdate):
    updated_at: datetime
