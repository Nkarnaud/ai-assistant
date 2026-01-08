"""Email processing service - orchestrates the email handling pipeline."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.oauth2 import get_valid_access_token
from ..crud.crud_draft_reply import crud_draft_replies
from ..crud.crud_email_message import crud_email_messages
from ..crud.crud_notification_preference import crud_notification_preferences
from ..models.draft_reply import DraftStatus
from ..models.email_message import EmailClassification
from ..schemas.draft_reply import DraftReplyCreateInternal
from ..schemas.email_message import EmailMessageCreateInternal, EmailMessageUpdateInternal
from .ai_service import AIService
from .calendar_event_extractor import CalendarEventExtractor
from .gmail_service import GmailService
from .notification_service import NotificationService


class EmailProcessor:
    """Process emails through classification, calendar extraction, and reply generation."""

    def __init__(
        self,
        ai_service: AIService,
        notification_service: NotificationService,
    ):
        """Initialize email processor.

        Parameters
        ----------
        ai_service: AIService
            AI service for classification and generation
        notification_service: NotificationService
            Service for sending notifications
        """
        self.ai_service = ai_service
        self.notification_service = notification_service
        self.calendar_extractor = CalendarEventExtractor(ai_service)

    async def process_email(self, user_id: int, message_id: str, db: AsyncSession) -> dict[str, any]:
        """Process a single email through the complete pipeline.

        Parameters
        ----------
        user_id: int
            User ID who owns the email
        message_id: str
            Gmail message ID
        db: AsyncSession
            Database session

        Returns
        -------
        dict[str, any]
            Processing result with actions taken
        """
        # Get user's Google credentials
        access_token = await get_valid_access_token(db, user_id, "google")
        if not access_token:
            return {"error": "No valid Google OAuth token found"}

        # Fetch email from Gmail
        gmail_service = GmailService(access_token)
        message = await gmail_service.get_message(message_id)

        # Extract email details
        headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "")
        from_email = headers.get("From", "")
        to_email = headers.get("To", "")
        thread_id = message.get("threadId", "")

        # Extract body
        body_text = self._extract_body(message)
        snippet = message.get("snippet", "")

        # Parse received date
        received_timestamp = int(message.get("internalDate", 0)) / 1000
        received_at = datetime.fromtimestamp(received_timestamp, UTC)

        # Check if already processed
        existing_email = await crud_email_messages.get(db=db, message_id=message_id)
        if existing_email:
            return {"status": "already_processed", "email_id": existing_email["id"]}

        # Store email in database
        email_data = EmailMessageCreateInternal(
            user_id=user_id,
            message_id=message_id,
            thread_id=thread_id,
            subject=subject,
            from_email=from_email,
            to_email=to_email,
            body_text=body_text,
            snippet=snippet,
            received_at=received_at,
        )

        db_email = await crud_email_messages.create(db=db, object=email_data)
        email_id = db_email["id"]

        result = {"email_id": email_id, "actions": []}

        # Get user preferences
        preferences = await crud_notification_preferences.get(db=db, user_id=user_id)

        # Step 1: Classify email
        classification_result = await self.ai_service.classify_email(subject, body_text, from_email)

        # Update email with classification
        await crud_email_messages.update(
            db=db,
            object=EmailMessageUpdateInternal(
                classification=classification_result["classification"],
                ai_analysis=classification_result.get("reasoning", ""),
                confidence_score=classification_result.get("confidence_score", 0.0),
                processed_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            id=email_id,
        )

        result["classification"] = classification_result["classification"]
        result["confidence"] = classification_result.get("confidence_score", 0.0)

        # Step 2: Handle based on classification
        classification = classification_result["classification"]

        # Calendar Planning - Extract and create event
        if classification == EmailClassification.CALENDAR_PLANNING.value:
            if settings.AUTO_CREATE_CALENDAR_EVENTS:
                event_result = await self.calendar_extractor.extract_and_create_event(
                    user_id=user_id,
                    email_message_id=email_id,
                    subject=subject,
                    body=body_text,
                    google_credentials=access_token,
                    db=db,
                )

                if event_result:
                    result["actions"].append("calendar_event_created")
                    result["event"] = event_result

                    # Send notification if enabled
                    if preferences and preferences.get("notify_calendar_event_created"):
                        await self.notification_service.notify_calendar_event_created(
                            user_id=user_id,
                            event_id=event_result["event_id"],
                            event_title=event_result["title"],
                            db=db,
                        )

        # Requires Reply - Generate draft
        elif classification == EmailClassification.REQUIRES_REPLY.value:
            # Get thread context for better replies
            thread_context = await self._get_thread_context(thread_id, gmail_service)

            reply_result = await self.ai_service.generate_reply(subject, body_text, from_email, thread_context)

            if reply_result and reply_result.get("content"):
                # Store draft reply
                draft_data = DraftReplyCreateInternal(
                    email_message_id=email_id,
                    user_id=user_id,
                    draft_content=reply_result["content"],
                    original_draft=reply_result["content"],
                    ai_model_used=settings.AI_MODEL_REPLY,
                    confidence_score=reply_result.get("confidence_score", 0.0),
                    analysis_context=reply_result.get("reasoning", ""),
                )

                db_draft = await crud_draft_replies.create(db=db, object=draft_data)
                result["actions"].append("draft_created")
                result["draft_id"] = db_draft["id"]

                # Check if should auto-approve
                if preferences and preferences.get("auto_approve_high_confidence"):
                    confidence_threshold = preferences.get("confidence_threshold", 0.95)
                    if reply_result.get("confidence_score", 0) >= confidence_threshold:
                        # Auto-approve and send
                        await self._send_draft(db_draft["id"], db, gmail_service, from_email)
                        result["actions"].append("auto_sent")
                    else:
                        # Send notification for manual review
                        if preferences.get("notify_new_draft"):
                            await self.notification_service.notify_new_draft(
                                user_id=user_id, draft_id=db_draft["id"], email_subject=subject, db=db
                            )
                elif preferences and preferences.get("notify_new_draft"):
                    await self.notification_service.notify_new_draft(
                        user_id=user_id, draft_id=db_draft["id"], email_subject=subject, db=db
                    )

        # Informational or Spam - Just mark as processed
        else:
            result["actions"].append("classified_only")

        return result

    def _extract_body(self, message: dict) -> str:
        """Extract plain text body from Gmail message.

        Parameters
        ----------
        message: dict
            Gmail message object

        Returns
        -------
        str
            Extracted body text
        """
        payload = message.get("payload", {})

        # Try to get plain text part
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    import base64

                    body_data = part.get("body", {}).get("data", "")
                    if body_data:
                        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

        # Fallback to body data
        import base64

        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

        return ""

    async def _get_thread_context(self, thread_id: str, gmail_service: GmailService) -> str | None:
        """Get previous messages in thread for context.

        Parameters
        ----------
        thread_id: str
            Gmail thread ID
        gmail_service: GmailService
            Gmail service instance

        Returns
        -------
        str | None
            Thread context or None
        """
        try:
            thread = await gmail_service.get_thread(thread_id)
            messages = thread.get("messages", [])

            if len(messages) <= 1:
                return None

            # Get last 3 messages for context
            context_messages = messages[-4:-1]
            context_parts = []

            for msg in context_messages:
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                subject = headers.get("Subject", "")
                from_email = headers.get("From", "")
                body = self._extract_body(msg)

                context_parts.append(f"From: {from_email}\nSubject: {subject}\n{body[:200]}...")

            return "\n\n---\n\n".join(context_parts)

        except Exception:
            return None

    async def _send_draft(self, draft_id: int, db: AsyncSession, gmail_service: GmailService, to_email: str) -> None:
        """Send a draft reply via Gmail.

        Parameters
        ----------
        draft_id: int
            Draft reply ID
        db: AsyncSession
            Database session
        gmail_service: GmailService
            Gmail service instance
        to_email: str
            Recipient email
        """
        from ..schemas.draft_reply import DraftReplyUpdateInternal

        draft = await crud_draft_replies.get(db=db, id=draft_id)
        if not draft:
            return

        try:
            # Send via Gmail
            await gmail_service.send_message(
                to=to_email, subject=f"Re: {draft.get('email_subject', '')}", body=draft["draft_content"]
            )

            # Update draft status
            await crud_draft_replies.update(
                db=db,
                object=DraftReplyUpdateInternal(
                    status=DraftStatus.APPROVED.value,
                    sent_at=datetime.now(UTC),
                    reviewed_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                ),
                id=draft_id,
            )

        except Exception as e:
            print(f"Failed to send draft {draft_id}: {e}")
