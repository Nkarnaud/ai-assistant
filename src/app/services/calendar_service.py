"""Google Calendar API service for managing calendar events."""

from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class CalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self, access_token: str):
        """Initialize Calendar service with OAuth2 credentials.

        Parameters
        ----------
        access_token: str
            Valid Google OAuth2 access token
        """
        self.credentials = Credentials(token=access_token)
        self.service = build("calendar", "v3", credentials=self.credentials)

    async def list_calendars(self) -> list[dict[str, Any]]:
        """List all calendars for the user.

        Returns
        -------
        list[dict[str, Any]]
            List of calendar objects
        """
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])
        return calendars

    async def get_events(
        self,
        calendar_id: str = "primary",
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 10,
        single_events: bool = True,
        order_by: str = "startTime",
    ) -> list[dict[str, Any]]:
        """Get events from a calendar.

        Parameters
        ----------
        calendar_id: str
            Calendar ID (default: "primary")
        time_min: datetime | None
            Lower bound for event start time
        time_max: datetime | None
            Upper bound for event start time
        max_results: int
            Maximum number of events to return
        single_events: bool
            Whether to expand recurring events into instances
        order_by: str
            Order of events ("startTime" or "updated")

        Returns
        -------
        list[dict[str, Any]]
            List of event objects
        """
        request_params: dict[str, Any] = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "singleEvents": single_events,
            "orderBy": order_by,
        }

        if time_min:
            request_params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            request_params["timeMax"] = time_max.isoformat() + "Z"

        events_result = self.service.events().list(**request_params).execute()
        events = events_result.get("items", [])
        return events

    async def get_event(self, event_id: str, calendar_id: str = "primary") -> dict[str, Any]:
        """Get a specific calendar event by ID.

        Parameters
        ----------
        event_id: str
            Calendar event ID
        calendar_id: str
            Calendar ID (default: "primary")

        Returns
        -------
        dict[str, Any]
            Event object
        """
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str = "primary",
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Create a new calendar event.

        Parameters
        ----------
        summary: str
            Event title/summary
        start: datetime
            Event start time
        end: datetime
            Event end time
        description: str | None
            Event description
        location: str | None
            Event location
        attendees: list[str] | None
            List of attendee email addresses
        calendar_id: str
            Calendar ID (default: "primary")
        timezone: str
            Timezone for the event (default: "UTC")

        Returns
        -------
        dict[str, Any]
            Created event object
        """
        event_body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": timezone},
        }

        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        event = self.service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return event

    async def update_event(
        self,
        event_id: str,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        calendar_id: str = "primary",
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Update an existing calendar event.

        Parameters
        ----------
        event_id: str
            Calendar event ID
        summary: str | None
            Event title/summary
        start: datetime | None
            Event start time
        end: datetime | None
            Event end time
        description: str | None
            Event description
        location: str | None
            Event location
        calendar_id: str
            Calendar ID (default: "primary")
        timezone: str
            Timezone for the event (default: "UTC")

        Returns
        -------
        dict[str, Any]
            Updated event object
        """
        # Get existing event
        event = await self.get_event(event_id, calendar_id)

        # Update fields
        if summary is not None:
            event["summary"] = summary
        if start is not None:
            event["start"] = {"dateTime": start.isoformat(), "timeZone": timezone}
        if end is not None:
            event["end"] = {"dateTime": end.isoformat(), "timeZone": timezone}
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location

        updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return updated_event

    async def delete_event(self, event_id: str, calendar_id: str = "primary") -> None:
        """Delete a calendar event.

        Parameters
        ----------
        event_id: str
            Calendar event ID
        calendar_id: str
            Calendar ID (default: "primary")
        """
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    async def list_upcoming_events(self, max_results: int = 10, calendar_id: str = "primary") -> list[dict[str, Any]]:
        """List upcoming events from now.

        Parameters
        ----------
        max_results: int
            Maximum number of events to return
        calendar_id: str
            Calendar ID (default: "primary")

        Returns
        -------
        list[dict[str, Any]]
            List of upcoming event objects
        """
        now = datetime.utcnow()
        return await self.get_events(
            calendar_id=calendar_id, time_min=now, max_results=max_results, single_events=True, order_by="startTime"
        )

    async def find_free_time(
        self, time_min: datetime, time_max: datetime, calendar_id: str = "primary"
    ) -> list[dict[str, Any]]:
        """Find free/busy information for a calendar.

        Parameters
        ----------
        time_min: datetime
            Start of time range
        time_max: datetime
            End of time range
        calendar_id: str
            Calendar ID (default: "primary")

        Returns
        -------
        list[dict[str, Any]]
            List of busy time blocks
        """
        body = {
            "timeMin": time_min.isoformat() + "Z",
            "timeMax": time_max.isoformat() + "Z",
            "items": [{"id": calendar_id}],
        }

        result = self.service.freebusy().query(body=body).execute()
        busy_times = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        return busy_times
