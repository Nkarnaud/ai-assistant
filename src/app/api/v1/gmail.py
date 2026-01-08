"""API endpoints for Gmail operations and watch management."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, get_google_credentials
from ...core.config import settings
from ...core.db.database import async_get_db
from ...crud.crud_gmail_watch_subscription import crud_gmail_watch_subscriptions
from ...schemas.gmail_watch_subscription import (
    GmailWatchSubscriptionCreateInternal,
    GmailWatchSubscriptionRead,
    GmailWatchSubscriptionUpdateInternal,
)
from ...services.gmail_service import GmailService

router = APIRouter(tags=["gmail"])


@router.post("/gmail/watch/setup", response_model=GmailWatchSubscriptionRead)
async def setup_gmail_watch(
    current_user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[str, Depends(get_google_credentials)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Set up Gmail push notifications via Google Pub/Sub.

    This enables real-time email monitoring. Watch expires after 7 days
    and needs renewal (handled automatically by background task).
    """
    # Check if user already has an active watch
    existing = await crud_gmail_watch_subscriptions.get(db=db, user_id=current_user["id"])

    if existing and existing.get("is_active"):
        raise HTTPException(status_code=400, detail="Gmail watch already active for this user")

    # Setup watch with Gmail API
    gmail_service = GmailService(credentials)
    topic_name = f"projects/{settings.GOOGLE_CLOUD_PROJECT}/topics/{settings.PUBSUB_TOPIC_NAME}"

    try:
        watch_response = await gmail_service.setup_watch(topic_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup Gmail watch: {str(e)}")

    # Extract expiration timestamp
    expiration_ms = int(watch_response.get("expiration", 0))
    expiration = datetime.fromtimestamp(expiration_ms / 1000, UTC)

    # Create or update subscription in database
    subscription_data = GmailWatchSubscriptionCreateInternal(
        user_id=current_user["id"],
        history_id=int(watch_response.get("historyId", 0)),
        expiration=expiration,
        topic_name=topic_name,
        is_active=True,
    )

    if existing:
        # Update existing
        subscription = await crud_gmail_watch_subscriptions.update(
            db=db,
            object=GmailWatchSubscriptionUpdateInternal(
                history_id=subscription_data.history_id,
                expiration=subscription_data.expiration,
                is_active=True,
                last_renewed_at=datetime.now(UTC),
                renewal_failures=0,
                updated_at=datetime.now(UTC),
            ),
            id=existing["id"],
        )
    else:
        # Create new
        subscription = await crud_gmail_watch_subscriptions.create(db=db, object=subscription_data)

    await db.commit()
    return subscription


@router.post("/gmail/watch/stop")
async def stop_gmail_watch(
    current_user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[str, Depends(get_google_credentials)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Stop Gmail push notifications.

    Stops receiving real-time email notifications from Gmail.
    """
    # Get active watch subscription
    subscription = await crud_gmail_watch_subscriptions.get(db=db, user_id=current_user["id"])

    if not subscription or not subscription.get("is_active"):
        raise HTTPException(status_code=404, detail="No active Gmail watch found")

    # Stop watch via Gmail API
    gmail_service = GmailService(credentials)

    try:
        await gmail_service.stop_watch()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop Gmail watch: {str(e)}")

    # Update subscription status
    await crud_gmail_watch_subscriptions.update(
        db=db,
        object=GmailWatchSubscriptionUpdateInternal(is_active=False, updated_at=datetime.now(UTC)),
        id=subscription["id"],
    )

    await db.commit()
    return {"message": "Gmail watch stopped successfully"}


@router.get("/gmail/watch/status", response_model=GmailWatchSubscriptionRead | None)
async def get_gmail_watch_status(
    current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict | None:
    """Get current Gmail watch subscription status.

    Returns subscription details including expiration time and active status.
    """
    subscription = await crud_gmail_watch_subscriptions.get(db=db, user_id=current_user["id"])
    return subscription


@router.get("/gmail/messages")
async def list_gmail_messages(
    current_user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[str, Depends(get_google_credentials)],
    query: str = "is:unread",
    max_results: int = 20,
) -> dict:
    """List Gmail messages with optional query filter.

    Query examples:
    - "is:unread" - Unread messages
    - "from:example@gmail.com" - From specific sender
    - "subject:meeting" - Contains word in subject
    - "after:2024/01/01" - After specific date
    """
    gmail_service = GmailService(credentials)

    try:
        messages = await gmail_service.list_messages(query=query, max_results=max_results)
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.get("/gmail/messages/{message_id}")
async def get_gmail_message(
    message_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[str, Depends(get_google_credentials)],
) -> dict:
    """Get full Gmail message details including body and headers."""
    gmail_service = GmailService(credentials)

    try:
        message = await gmail_service.get_message(message_id)
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message: {str(e)}")


@router.post("/gmail/messages/send")
async def send_gmail_message(
    to: str,
    subject: str,
    body: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[str, Depends(get_google_credentials)],
    thread_id: str | None = None,
) -> dict:
    """Send an email via Gmail.

    Parameters:
    - to: Recipient email address
    - subject: Email subject
    - body: Email body (plain text)
    - thread_id: Optional - reply to existing thread
    """
    gmail_service = GmailService(credentials)

    try:
        result = await gmail_service.send_message(to=to, subject=subject, body=body, thread_id=thread_id)
        return {"message": "Email sent successfully", "message_id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
