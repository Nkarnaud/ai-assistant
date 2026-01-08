from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class OAuthTokenBase(BaseModel):
    provider: Annotated[str, Field(max_length=50, examples=["google"])]
    access_token: str
    refresh_token: str | None = None
    token_type: Annotated[str, Field(max_length=50, examples=["Bearer"])] = "Bearer"
    expires_at: datetime
    scopes: list[str] = []


class OAuthToken(OAuthTokenBase):
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None


class OAuthTokenRead(BaseModel):
    id: int
    user_id: int
    provider: str
    token_type: str
    expires_at: datetime
    scopes: list[str]
    created_at: datetime
    updated_at: datetime | None


class OAuthTokenCreate(OAuthTokenBase):
    model_config = ConfigDict(extra="forbid")


class OAuthTokenCreateInternal(OAuthTokenBase):
    user_id: int


class OAuthTokenUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_at: datetime | None = None
    scopes: list[str] | None = None


class OAuthTokenUpdateInternal(OAuthTokenUpdate):
    updated_at: datetime
