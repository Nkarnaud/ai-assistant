"""Service for extracting and creating calendar events from emails."""

from typing import Any

from dateutil import parser
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..crud.crud_calendar_event import crud_calendar_events
from ..schemas.calendar_event import CalendarEventCreateInternal
from .ai_service import AIService
from .calendar_service import CalendarService


class CalendarEventExtractor:
    """Extract calendar events from emails and create them in Google Calendar."""

    def __init__(self, ai_service: AIService):
        """Initialize with AI service.

        Parameters
        ----------
        ai_service: AIService
            AI service for event extraction
        """
        self.ai_service = ai_service

    async def extract_and_create_event(
        self,
        user_id: int,
        email_message_id: int,
        subject: str,
        body: str,
        google_credentials: str,
        db: AsyncSession,
    ) -> dict[str, Any] | None:
        """Extract event from email and create it in Google Calendar.

        Parameters
        ----------
        user_id: int
            User ID
        email_message_id: int
            Email message ID
        subject: str
            Email subject
        body: str
            Email body
        google_credentials: str
            Valid Google OAuth access token
        db: AsyncSession
            Database session

        Returns
        -------
        dict[str, Any] | None
            Created event details or None if no event extracted
        """
        # Extract event using AI
        extracted_data = await self.ai_service.extract_calendar_event(subject, body)

        if not extracted_data:
            return None

        # Validate confidence threshold
        if extracted_data.get("confidence_score", 0) < settings.AI_CONFIDENCE_THRESHOLD:
            return None

        try:
            # Parse datetime strings
            start_time = parser.parse(extracted_data["start_time"])
            end_time = parser.parse(extracted_data["end_time"])

            # Create event in Google Calendar
            calendar_service = CalendarService(google_credentials)

            google_event = await calendar_service.create_event(
                summary=extracted_data["title"],
                start=start_time,
                end=end_time,
                description=extracted_data.get("description"),
                location=extracted_data.get("location"),
                attendees=extracted_data.get("attendees", []),
                timezone=extracted_data.get("timezone", "UTC"),
            )

            # Store in database
            event_data = CalendarEventCreateInternal(
                user_id=user_id,
                email_message_id=email_message_id,
                google_event_id=google_event["id"],
                calendar_id="primary",
                title=extracted_data["title"],
                description=extracted_data.get("description"),
                location=extracted_data.get("location"),
                start_time=start_time,
                end_time=end_time,
                timezone=extracted_data.get("timezone", "UTC"),
                attendees=",".join(extracted_data.get("attendees", [])),
                created_from_email=True,
                auto_created=settings.AUTO_CREATE_CALENDAR_EVENTS,
                confidence_score=extracted_data.get("confidence_score"),
            )

            db_event = await crud_calendar_events.create(db=db, object=event_data)

            return {
                "event_id": db_event["id"],
                "google_event_id": google_event["id"],
                "title": extracted_data["title"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "confidence_score": extracted_data.get("confidence_score"),
            }

        except Exception as e:
            # Log error but don't fail the entire email processing
            print(f"Failed to create calendar event: {e}")
            return None

    async def should_create_event(self, confidence_score: float) -> bool:
        """Check if event should be auto-created based on settings.

        Parameters
        ----------
        confidence_score: float
            AI confidence score for event extraction

        Returns
        -------
        bool
            True if event should be created
        """
        if not settings.AUTO_CREATE_CALENDAR_EVENTS:
            return False

        if settings.REQUIRE_EVENT_CONFIRMATION:
            return False

        return confidence_score >= settings.AI_CONFIDENCE_THRESHOLD
