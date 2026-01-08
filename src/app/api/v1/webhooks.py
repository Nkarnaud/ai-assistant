"""Webhook endpoints for external services (Gmail Pub/Sub)."""

import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_gmail_watch_subscription import crud_gmail_watch_subscriptions

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/gmail")
async def gmail_push_notification(request: Request, db: Annotated[AsyncSession, Depends(async_get_db)]) -> dict:
    """Receive Gmail push notifications from Google Pub/Sub.

    This endpoint is called by Google Cloud Pub/Sub when new emails arrive.

    Parameters
    ----------
    request: Request
        FastAPI request containing Pub/Sub message
    db: AsyncSession
        Database session

    Returns
    -------
    dict
        Acknowledgment response
    """
    try:
        # Parse Pub/Sub message
        body = await request.json()
        message = body.get("message", {})

        if not message:
            return {"status": "no_message"}

        # Decode message data
        data_b64 = message.get("data", "")
        if data_b64:
            data_str = base64.b64decode(data_b64).decode("utf-8")
            data = json.loads(data_str)
        else:
            return {"status": "no_data"}

        email_address = data.get("emailAddress")
        history_id = data.get("historyId")

        if not email_address or not history_id:
            return {"status": "invalid_data"}

        # Find user by email address
        # Note: You'll need to add a method to find user by their Google email
        # For now, we'll get the subscription and process

        # Get subscription by history tracking
        subscription = await crud_gmail_watch_subscriptions.get(db=db, history_id=history_id)

        if not subscription:
            # Find any active subscription (we'll improve this)
            subscriptions = await crud_gmail_watch_subscriptions.get_multi(db=db, is_active=True, limit=1)
            if subscriptions and subscriptions.get("data"):
                subscription = subscriptions["data"][0]
            else:
                return {"status": "no_subscription_found"}

        user_id = subscription["user_id"]

        # Queue email processing task
        # Import here to avoid circular dependency
        from ...core.celery_tasks import process_new_emails_task

        process_new_emails_task.delay(user_id, int(history_id))

        return {"status": "queued", "user_id": user_id, "history_id": history_id}

    except Exception as e:
        print(f"Error processing Gmail webhook: {e}")
        return {"status": "error", "message": str(e)}
