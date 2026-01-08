"""Celery tasks for background email processing and notifications."""

from datetime import UTC, datetime, timedelta

from ..crud.crud_calendar_event import crud_calendar_events
from ..crud.crud_gmail_watch_subscription import crud_gmail_watch_subscriptions
from ..crud.crud_notification_preference import crud_notification_preferences
from ..services.ai_service import AIService
from ..services.email_processor import EmailProcessor
from ..services.gmail_service import GmailService
from ..services.notification_service import NotificationService
from .celery_app import celery_app
from .config import settings
from .db.database import async_get_db
from .oauth2 import get_valid_access_token


@celery_app.task(name="app.core.celery_tasks.process_new_emails")
def process_new_emails_task(user_id: int, history_id: int) -> dict:
    """Process new emails for a user (background task).

    Parameters
    ----------
    user_id: int
        User ID
    history_id: int
        Gmail history ID to process from

    Returns
    -------
    dict
        Processing result
    """
    import asyncio

    async def _process():
        async for db in async_get_db():
            try:
                # Get Google credentials
                access_token = await get_valid_access_token(db, user_id, "google")
                if not access_token:
                    return {"error": "No valid credentials"}

                # Get message history
                gmail_service = GmailService(access_token)
                history = await gmail_service.get_history(history_id)

                # Initialize services
                ai_service = AIService()
                notification_service = NotificationService()
                processor = EmailProcessor(ai_service, notification_service)

                processed_count = 0
                for history_record in history:
                    messages_added = history_record.get("messagesAdded", [])
                    for msg_record in messages_added:
                        message_id = msg_record.get("message", {}).get("id")
                        if message_id:
                            await processor.process_email(user_id, message_id, db)
                            processed_count += 1

                await db.commit()
                return {"processed": processed_count}

            except Exception as e:
                await db.rollback()
                return {"error": str(e)}

    return asyncio.run(_process())


@celery_app.task(name="app.core.celery_tasks.check_upcoming_events")
def check_upcoming_events() -> dict:
    """Check for upcoming events and send notifications."""
    import asyncio

    async def _check():
        async for db in async_get_db():
            try:
                notification_service = NotificationService()
                now = datetime.now(UTC)

                # Check for events in next 24 hours
                time_window = now + timedelta(hours=24)

                # Get all upcoming events
                events = await crud_calendar_events.get_multi(
                    db=db, start_time__gte=now, start_time__lte=time_window, notification_sent=False, limit=100
                )

                sent_count = 0
                for event in events.get("data", []):
                    user_id = event["user_id"]
                    start_time = event["start_time"]

                    # Get user preferences
                    prefs = await crud_notification_preferences.get(db=db, user_id=user_id)
                    if not prefs or not prefs.get("push_notifications"):
                        continue

                    # Calculate minutes until event
                    time_diff = start_time - now
                    minutes_until = int(time_diff.total_seconds() / 60)

                    # Check notification preferences
                    should_notify = False
                    if prefs.get("notify_15_min_before") and 10 <= minutes_until <= 20:
                        should_notify = True
                    elif prefs.get("notify_1_hour_before") and 55 <= minutes_until <= 65:
                        should_notify = True
                    elif prefs.get("notify_1_day_before") and 1435 <= minutes_until <= 1445:
                        should_notify = True

                    if should_notify:
                        await notification_service.notify_upcoming_event(
                            user_id=user_id,
                            event_title=event["title"],
                            start_time=start_time.strftime("%Y-%m-%d %H:%M"),
                            minutes_before=minutes_until,
                            db=db,
                        )

                        # Mark as notified
                        from ..schemas.calendar_event import CalendarEventUpdateInternal

                        await crud_calendar_events.update(
                            db=db,
                            object=CalendarEventUpdateInternal(
                                notification_sent=True, notification_sent_at=now, updated_at=now
                            ),
                            id=event["id"],
                        )
                        sent_count += 1

                await db.commit()
                return {"notifications_sent": sent_count}

            except Exception as e:
                await db.rollback()
                return {"error": str(e)}

    return asyncio.run(_check())


@celery_app.task(name="app.core.celery_tasks.renew_gmail_watch_subscriptions")
def renew_gmail_watch_subscriptions() -> dict:
    """Renew Gmail watch subscriptions (run daily)."""
    import asyncio

    async def _renew():
        async for db in async_get_db():
            try:
                # Get subscriptions expiring in next 2 days
                expiry_threshold = datetime.now(UTC) + timedelta(days=2)

                subscriptions = await crud_gmail_watch_subscriptions.get_multi(
                    db=db, is_active=True, expiration__lte=expiry_threshold, limit=100
                )

                renewed_count = 0
                for sub in subscriptions.get("data", []):
                    user_id = sub["user_id"]

                    # Get Google credentials
                    access_token = await get_valid_access_token(db, user_id, "google")
                    if not access_token:
                        continue

                    # Renew watch
                    gmail_service = GmailService(access_token)
                    topic_name = f"projects/{settings.GOOGLE_CLOUD_PROJECT}/topics/{settings.PUBSUB_TOPIC_NAME}"

                    try:
                        watch_response = await gmail_service.setup_watch(topic_name)

                        # Update subscription
                        from ..schemas.gmail_watch_subscription import GmailWatchSubscriptionUpdateInternal

                        expiration_ms = int(watch_response.get("expiration", 0))
                        expiration = datetime.fromtimestamp(expiration_ms / 1000, UTC)

                        await crud_gmail_watch_subscriptions.update(
                            db=db,
                            object=GmailWatchSubscriptionUpdateInternal(
                                history_id=int(watch_response.get("historyId", 0)),
                                expiration=expiration,
                                last_renewed_at=datetime.now(UTC),
                                renewal_failures=0,
                                updated_at=datetime.now(UTC),
                            ),
                            id=sub["id"],
                        )
                        renewed_count += 1

                    except Exception:
                        # Increment failure count
                        from ..schemas.gmail_watch_subscription import GmailWatchSubscriptionUpdateInternal

                        failures = sub.get("renewal_failures", 0) + 1
                        await crud_gmail_watch_subscriptions.update(
                            db=db,
                            object=GmailWatchSubscriptionUpdateInternal(
                                renewal_failures=failures,
                                is_active=failures < 3,
                                updated_at=datetime.now(UTC),
                            ),
                            id=sub["id"],
                        )

                await db.commit()
                return {"renewed": renewed_count}

            except Exception as e:
                await db.rollback()
                return {"error": str(e)}

    return asyncio.run(_renew())
