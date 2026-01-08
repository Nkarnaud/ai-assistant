from fastcrud import FastCRUD

from ..models.calendar_event import CalendarEvent
from ..schemas.calendar_event import (
    CalendarEventCreateInternal,
    CalendarEventRead,
    CalendarEventUpdate,
    CalendarEventUpdateInternal,
)

CRUDCalendarEvent = FastCRUD[
    CalendarEvent,
    CalendarEventCreateInternal,
    CalendarEventUpdate,
    CalendarEventUpdateInternal,
    CalendarEventRead,
    CalendarEventRead,
]
crud_calendar_events = CRUDCalendarEvent(CalendarEvent)
