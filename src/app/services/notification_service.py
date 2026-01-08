"""Service for sending push notifications to users."""

import json
from typing import Any

from pywebpush import WebPushException, webpush
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..crud.crud_push_subscription import crud_push_subscriptions


class NotificationService:
    """Service for managing and sending push notifications."""

    def __init__(self):
        """Initialize notification service."""
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY.get_secret_value()
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_claims = {"sub": f"mailto:{settings.VAPID_CONTACT_EMAIL}"}

    async def send_notification(
        self, user_id: int, title: str, body: str, data: dict[str, Any] | None, db: AsyncSession
    ) -> dict[str, int]:
        """Send push notification to all user's active subscriptions.

        Parameters
        ----------
        user_id: int
            User ID to send notification to
        title: str
            Notification title
        body: str
            Notification body text
        data: dict[str, Any] | None
            Additional data payload
        db: AsyncSession
            Database session

        Returns
        -------
        dict[str, int]
            Result with success and failure counts
        """
        # Get all active push subscriptions for user
        subscriptions = await crud_push_subscriptions.get_multi(db=db, user_id=user_id, is_active=True)

        if not subscriptions or not subscriptions.get("data"):
            return {"success": 0, "failures": 0}

        payload = {"title": title, "body": body, "data": data or {}}

        success_count = 0
        failure_count = 0

        for subscription in subscriptions["data"]:
            try:
                subscription_info = {
                    "endpoint": subscription["endpoint"],
                    "keys": {"p256dh": subscription["p256dh_key"], "auth": subscription["auth_key"]},
                }

                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims,
                )

                success_count += 1

                # Update last_used_at
                from datetime import UTC, datetime

                from ..schemas.push_subscription import PushSubscriptionUpdateInternal

                await crud_push_subscriptions.update(
                    db=db,
                    object=PushSubscriptionUpdateInternal(
                        last_used_at=datetime.now(UTC), updated_at=datetime.now(UTC)
                    ),
                    id=subscription["id"],
                )

            except WebPushException as e:
                failure_count += 1

                # If subscription is expired/invalid, increment failure count
                if e.response and e.response.status_code in [404, 410]:
                    from ..schemas.push_subscription import PushSubscriptionUpdateInternal

                    current_failures = subscription.get("failure_count", 0) + 1

                    # Deactivate after 3 failures
                    is_active = current_failures < 3

                    await crud_push_subscriptions.update(
                        db=db,
                        object=PushSubscriptionUpdateInternal(
                            failure_count=current_failures, is_active=is_active, updated_at=datetime.now(UTC)
                        ),
                        id=subscription["id"],
                    )

        return {"success": success_count, "failures": failure_count}

    async def notify_new_draft(self, user_id: int, draft_id: int, email_subject: str, db: AsyncSession) -> None:
        """Send notification for new draft reply.

        Parameters
        ----------
        user_id: int
            User ID
        draft_id: int
            Draft reply ID
        email_subject: str
            Original email subject
        db: AsyncSession
            Database session
        """
        await self.send_notification(
            user_id=user_id,
            title="New Draft Reply",
            body=f"AI generated a reply for: {email_subject}",
            data={"type": "new_draft", "draft_id": draft_id},
            db=db,
        )

    async def notify_calendar_event_created(
        self, user_id: int, event_id: int, event_title: str, db: AsyncSession
    ) -> None:
        """Send notification for calendar event created from email.

        Parameters
        ----------
        user_id: int
            User ID
        event_id: int
            Calendar event ID
        event_title: str
            Event title
        db: AsyncSession
            Database session
        """
        await self.send_notification(
            user_id=user_id,
            title="Calendar Event Created",
            body=f"Event added to your calendar: {event_title}",
            data={"type": "calendar_event_created", "event_id": event_id},
            db=db,
        )

    async def notify_upcoming_event(
        self, user_id: int, event_title: str, start_time: str, minutes_before: int, db: AsyncSession
    ) -> None:
        """Send notification for upcoming calendar event.

        Parameters
        ----------
        user_id: int
            User ID
        event_title: str
            Event title
        start_time: str
            Event start time (formatted)
        minutes_before: int
            Minutes before event
        db: AsyncSession
            Database session
        """
        if minutes_before < 60:
            time_str = f"in {minutes_before} minutes"
        elif minutes_before < 1440:
            hours = minutes_before // 60
            time_str = f"in {hours} hour{'s' if hours > 1 else ''}"
        else:
            days = minutes_before // 1440
            time_str = f"in {days} day{'s' if days > 1 else ''}"

        await self.send_notification(
            user_id=user_id,
            title=f"Upcoming Event: {event_title}",
            body=f"Starts {time_str} at {start_time}",
            data={"type": "upcoming_event", "minutes_before": minutes_before},
            db=db,
        )
