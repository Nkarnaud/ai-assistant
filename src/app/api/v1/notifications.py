"""API endpoints for notification management."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...crud.crud_notification_preference import crud_notification_preferences
from ...crud.crud_push_subscription import crud_push_subscriptions
from ...schemas.notification_preference import (
    NotificationPreferenceCreateInternal,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationPreferenceUpdateInternal,
)
from ...schemas.push_subscription import PushSubscriptionCreate, PushSubscriptionCreateInternal, PushSubscriptionRead

router = APIRouter(tags=["notifications"])


@router.get("/notifications/preferences", response_model=NotificationPreferenceRead)
async def get_preferences(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict:
    """Get user's notification preferences."""
    prefs = await crud_notification_preferences.get(db=db, user_id=current_user["id"])

    if not prefs:
        # Create default preferences
        default_prefs = NotificationPreferenceCreateInternal(user_id=current_user["id"])
        prefs = await crud_notification_preferences.create(db=db, object=default_prefs)

    return prefs


@router.put("/notifications/preferences", response_model=NotificationPreferenceRead)
async def update_preferences(
    preferences: NotificationPreferenceUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Update notification preferences."""
    existing = await crud_notification_preferences.get(db=db, user_id=current_user["id"])

    if not existing:
        raise HTTPException(status_code=404, detail="Preferences not found")

    updated = await crud_notification_preferences.update(
        db=db,
        object=NotificationPreferenceUpdateInternal(**preferences.model_dump(), updated_at=datetime.now(UTC)),
        id=existing["id"],
    )
    return updated


@router.post("/notifications/subscribe", response_model=PushSubscriptionRead)
async def subscribe_push(
    subscription: PushSubscriptionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Subscribe to push notifications."""
    sub_data = PushSubscriptionCreateInternal(user_id=current_user["id"], **subscription.model_dump())
    created = await crud_push_subscriptions.create(db=db, object=sub_data)
    return created


@router.get("/notifications/subscriptions", response_model=list[PushSubscriptionRead])
async def list_subscriptions(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> list:
    """List user's push subscriptions."""
    subs = await crud_push_subscriptions.get_multi(db=db, user_id=current_user["id"])
    return subs.get("data", [])
