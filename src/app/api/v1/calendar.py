"""API endpoints for calendar event management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, get_google_credentials
from ...core.db.database import async_get_db
from ...crud.crud_calendar_event import crud_calendar_events
from ...schemas.calendar_event import CalendarEventCreate, CalendarEventCreateInternal, CalendarEventRead
from ...services.calendar_service import CalendarService
from ..models.calendar_event import CalendarEvent

router = APIRouter(tags=["calendar"])


@router.get("/calendar/events", response_model=dict)
async def list_events(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """List calendar events for current user."""
    events = await crud_calendar_events.get_multi(db=db, offset=skip, limit=limit, user_id=current_user["id"])
    return events


@router.get("/calendar/upcoming", response_model=list[CalendarEventRead])
async def get_upcoming_events(
    current_user: Annotated[dict, Depends(get_current_user)],
    google_credentials: Annotated[str, Depends(get_google_credentials)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    max_results: int = 10,
) -> list:
    """Get upcoming calendar events from Google Calendar."""
    calendar_service = CalendarService(google_credentials)
    upcoming = await calendar_service.list_upcoming_events(max_results=max_results)
    return upcoming


@router.post("/calendar/events", response_model=CalendarEventRead)
async def create_event(
    event_data: CalendarEventCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    google_credentials: Annotated[str, Depends(get_google_credentials)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> CalendarEvent:
    """Create a new calendar event."""
    calendar_service = CalendarService(google_credentials)

    google_event = await calendar_service.create_event(
        summary=event_data.title,
        start=event_data.start_time,
        end=event_data.end_time,
        description=event_data.description,
        location=event_data.location,
        timezone=event_data.timezone,
    )

    db_event = CalendarEventCreateInternal(
        user_id=current_user["id"],
        email_message_id=None,
        google_event_id=google_event["id"],
        **event_data.model_dump(),
    )

    created = await crud_calendar_events.create(db=db, object=db_event)
    return created
