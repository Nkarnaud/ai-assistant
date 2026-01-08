# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simplified FastAPI application for an AI assistant that connects to Gmail and calendar services. It's built on FastAPI with async PostgreSQL, Redis caching, and JWT authentication.

**Tech stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL, Redis, Docker

## Development Commands

### Setup & Running

```bash
# Initial setup (interactive)
./setup.py

# Or specify deployment type directly
./setup.py local      # Local development with Uvicorn (auto-reload)
./setup.py staging    # Staging with Gunicorn managing Uvicorn workers
./setup.py production # Production with NGINX

# Start application (after setup)
docker compose up

# Run locally without Docker (requires uv package manager)
uv sync && uv run uvicorn src.app.main:app --reload

# Create first superuser
docker compose run --rm create_superuser
```

### Database Migrations

```bash
# Generate and apply migrations (run from src/ directory)
cd src && uv run alembic revision --autogenerate && uv run alembic upgrade head

# Apply existing migrations only
cd src && uv run alembic upgrade head

# Rollback one migration
cd src && uv run alembic downgrade -1
```

### Testing

```bash
# Run tests via Docker
docker compose run --rm pytest

# Run locally
uv run pytest ./tests

# Run specific test file
uv run pytest tests/test_user.py
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check src/

# Format with ruff
uv run ruff format src/

# Type check with mypy
uv run mypy src/
```

## Architecture Overview

### Application Structure

The application follows a layered architecture:

1. **Entry Point:** `src/app/main.py` - Creates FastAPI app with settings
2. **Core Setup:** `src/app/core/setup.py` - App factory, lifespan management, middleware configuration
3. **Configuration:** `src/app/core/config.py` - Pydantic settings classes (loads from `src/.env`)
4. **Database:** `src/app/core/db/database.py` - SQLAlchemy async engine and session factory
5. **API Routes:** `src/app/api/v1/` - Versioned API endpoints (health, login, logout, oauth, users)
6. **Services:** `src/app/services/` - Google API service wrappers (Gmail, Calendar)
7. **CRUD Layer:** `src/app/crud/` - FastCRUD instances for database operations
8. **Models:** `src/app/models/` - SQLAlchemy ORM models (User, OAuthToken)
9. **Schemas:** `src/app/schemas/` - Pydantic schemas for validation and serialization

### Key Architectural Patterns

**Application Factory Pattern:**
- `create_application()` in `src/app/core/setup.py` builds the FastAPI app
- Accepts settings objects and configures middleware, CORS, docs, etc.
- `lifespan_factory()` creates async context manager for startup/shutdown

**Dependency Injection:**
- `async_get_db()` provides async database sessions
- `get_current_user()` validates JWT and returns user dict
- `get_optional_user()` returns user if authenticated, None otherwise
- `get_current_superuser()` enforces superuser access

**FastCRUD Pattern:**
- All CRUD operations use FastCRUD generics from `fastcrud` library
- Example: `crud_users = CRUDUser(User)` in `src/app/crud/crud_users.py`
- Provides: get, get_multi, create, update, delete, count, exists, get_joined, etc.
- Schemas passed as type hints: `UserCreateInternal`, `UserUpdate`, `UserRead`, etc.

### Authentication & Authorization

**Dual Authentication System:**

1. **JWT Token Flow (Traditional):**
   - Access tokens: 30 min expiry (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
   - Refresh tokens: 7 days expiry (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
   - Refresh tokens stored in httpOnly cookies
   - Token blacklist prevents reuse after logout (stored in DB and Redis)
   - Login endpoint: `POST /api/v1/login`
   - Password-based authentication with bcrypt hashing

2. **OAuth2 Flow (Google):**
   - Google OAuth2 integration for Gmail and Calendar access
   - OAuth tokens encrypted at rest using Fernet (cryptography library)
   - Separate `oauth_token` table stores encrypted access/refresh tokens per user
   - Automatic token refresh when expired
   - OAuth endpoints:
     - `GET /api/v1/auth/google` - Start OAuth flow
     - `GET /api/v1/auth/callback` - Handle Google callback (creates/logs in user)
     - `POST /api/v1/auth/link-google` - Link Google to existing user
     - `POST /api/v1/auth/unlink-google` - Unlink Google account

**Security:**
- JWT creation/validation in `src/app/core/security.py`
- OAuth2 service in `src/app/core/oauth2.py`
- Token encryption/decryption utilities in `src/app/core/security.py` (`encrypt_token`, `decrypt_token`)
- Password hashing with bcrypt
- Token verification in dependencies (`get_current_user`, `get_current_superuser`, `get_google_credentials`)

**OAuth Configuration (in `src/.env`):**
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
TOKEN_ENCRYPTION_KEY=your_44_char_fernet_key
```

Generate encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### Caching Strategy

**Two-Layer Caching:**
1. **Server-side Redis cache:** Decorator-based endpoint caching
   - Use `@cache()` decorator on endpoints
   - Configured via `REDIS_CACHE_HOST`, `REDIS_CACHE_PORT`
2. **Client-side cache headers:** ClientCacheMiddleware sets Cache-Control headers
   - Max-age configurable via `CLIENT_CACHE_MAX_AGE`

**Cache utilities:** `src/app/core/utils/cache.py`

### Database Models

**Base Models:**
- All models inherit from `Base` (SQLAlchemy DeclarativeBase + MappedAsDataclass)
- Common fields: `id`, `created_at`, `updated_at`, `deleted_at`, `is_deleted`, `uuid`
- Soft delete pattern: Set `is_deleted=True`, `deleted_at=datetime.now(UTC)`

**Key Models:**
- `User`: Main user table with username, email, hashed_password, is_superuser, oauth_provider, oauth_sub
- `OAuthToken`: Stores encrypted OAuth2 tokens (access_token, refresh_token, expires_at, scopes)
- `TokenBlacklist`: Stores invalidated JWTs (in `src/app/core/db/token_blacklist.py`)

### Environment Configuration

**ENVIRONMENT Variable Controls Behavior:**
- `local`: API docs at `/docs` and `/redoc` (no auth required)
- `staging`: Docs protected by superuser authentication
- `production`: Docs completely disabled

**Configuration Loading:**
- Settings loaded from `src/.env` file
- Pydantic Settings classes in `src/app/core/config.py`
- All settings accessed via `settings` singleton

## Important Implementation Notes

### When Adding New Endpoints

1. Create endpoint in `src/app/api/v1/your_endpoint.py`
2. Add router to `src/app/api/v1/__init__.py`
3. Create Pydantic schemas in `src/app/schemas/`
4. Create SQLAlchemy model in `src/app/models/` (if needed)
5. Create FastCRUD instance in `src/app/crud/` (if needed)
6. Run migration: `cd src && uv run alembic revision --autogenerate && uv run alembic upgrade head`

### When Adding New Models

1. Define model in `src/app/models/` inheriting from `Base`
2. Import model in `src/app/models/__init__.py`
3. Import model in `src/app/core/setup.py` (line 15: `from ..models import *`)
4. Create corresponding Pydantic schemas
5. Create CRUD instance using FastCRUD
6. Generate and apply migration

### Testing Considerations

- Tests use conftest.py for fixtures
- Mock helpers in `tests/helpers/mocks.py`
- Test generators in `tests/helpers/generators.py`
- Run tests via Docker to ensure proper environment setup

## Common Patterns

**Async Database Operations:**
```python
async def get_user(db: Annotated[AsyncSession, Depends(async_get_db)], user_id: int):
    return await crud_users.get(db=db, id=user_id, is_deleted=False)
```

**Protected Endpoints:**
```python
@router.get("/protected")
async def protected_route(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    return {"user": current_user}
```

**Cached Endpoints:**
```python
@router.get("/cached")
@cache(ttl=3600)
async def cached_route():
    return {"data": "expensive_computation"}
```

## Docker Configuration

The application supports three deployment modes, configured via `./setup.py`:

1. **Local:** Single Uvicorn process with auto-reload
2. **Staging:** Gunicorn managing multiple Uvicorn workers
3. **Production:** NGINX reverse proxy + Gunicorn + Uvicorn workers

Docker Compose services:
- `web`: Main FastAPI application
- `db`: PostgreSQL 13
- `redis`: Redis Alpine
- `nginx`: NGINX (production only)
- `create_superuser`: One-off command to create admin
- `pytest`: One-off command to run tests

## Package Management

This project uses `uv` as the Python package manager. Install dependencies:
```bash
uv sync
```

Dependencies defined in `pyproject.toml` with dev dependencies in `[project.optional-dependencies]`.

## Development Best Practices

- Use comment sparing. only comment complex code.

### Database

- The database model is defined in the @src/app/models/ files.
Reference it anytime you need to understand the structure of the data store in the database

## AI Email Assistant System

This is a comprehensive AI-powered email assistant that automatically processes incoming emails, classifies them, extracts calendar events, and generates intelligent reply drafts.

### System Architecture

**Key Components:**
1. **Gmail Push Notifications** - Real-time email monitoring via Google Pub/Sub
2. **AI Classification** - Categorizes emails (calendar planning, requires reply, informational, spam)
3. **Calendar Event Extraction** - Auto-creates calendar events from meeting emails
4. **AI Reply Generation** - Creates draft replies for review/approval
5. **Push Notifications** - Alerts for drafts, events, and upcoming meetings
6. **Background Tasks** - Celery for async processing

**Email Processing Pipeline:**
```
New Email → Pub/Sub Webhook → Celery Task → Email Processor
    ↓
AI Classification
    ↓
If CALENDAR_PLANNING → Extract Event → Create in Google Calendar → Notify
If REQUIRES_REPLY → Generate Draft → Store for Approval → Notify
If INFORMATIONAL → Mark as Processed
```

### Google API Services

**Core Services:**

1. **AIService** (`src/app/services/ai_service.py`)
   - `classify_email()` - AI classification into categories
   - `generate_reply()` - Create draft email replies
   - `extract_calendar_event()` - Extract event details from email text
   - Supports Claude (Anthropic) and OpenAI models

2. **EmailProcessor** (`src/app/services/email_processor.py`)
   - `process_email()` - Main orchestration pipeline
   - Handles classification, event extraction, reply generation
   - Manages user preferences and notifications

3. **CalendarEventExtractor** (`src/app/services/calendar_event_extractor.py`)
   - `extract_and_create_event()` - End-to-end event creation
   - Validates confidence thresholds
   - Syncs with Google Calendar

4. **NotificationService** (`src/app/services/notification_service.py`)
   - `send_notification()` - Web push notifications
   - `notify_new_draft()` - Alert for new draft replies
   - `notify_calendar_event_created()` - Event creation alerts
   - `notify_upcoming_event()` - Upcoming event reminders

5. **GmailService** (`src/app/services/gmail_service.py`)
   - `setup_watch()` / `stop_watch()` - Gmail push notifications
   - `get_history()` - Fetch new emails since history ID
   - Standard Gmail operations (list, get, send, etc.)

6. **CalendarService** (`src/app/services/calendar_service.py`)
   - Full Google Calendar API wrapper
   - Create, read, update, delete events
   - Find free/busy times

### Using Google APIs in Endpoints

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from ..api.dependencies import get_google_credentials
from ..services.gmail_service import GmailService

router = APIRouter(tags=["gmail"])

@router.get("/emails")
async def list_emails(
    credentials: Annotated[str, Depends(get_google_credentials)],
    query: str = "is:unread"
):
    gmail = GmailService(credentials)
    messages = await gmail.list_messages(query=query, max_results=10)
    return {"messages": messages}
```

**Key Points:**
- Use `get_google_credentials` dependency to get valid OAuth token (auto-refreshes if expired)
- Create service instance with credentials: `GmailService(credentials)` or `CalendarService(credentials)`
- All service methods are async and should be awaited
- Services handle Google API client initialization and error handling

### OAuth2 Setup Checklist

1. Create Google Cloud Console project
2. Enable Gmail API and Calendar API
3. Configure OAuth consent screen
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/callback`
6. Copy Client ID and Client Secret to `src/.env`
7. Generate encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
8. Add encryption key to `src/.env` as `TOKEN_ENCRYPTION_KEY`
9. Run migration: `docker compose exec web bash -c "cd /app && alembic upgrade head"` (if not auto-applied)

### API Endpoints

**Gmail Operations:**
- `POST /api/v1/gmail/watch/setup` - Enable real-time email monitoring via Pub/Sub
  - **Related Tasks:** Start receiving push notifications for new emails
  - Creates watch subscription (expires in 7 days, auto-renewed)

- `POST /api/v1/gmail/watch/stop` - Disable email monitoring
  - **Related Tasks:** Stop receiving push notifications

- `GET /api/v1/gmail/watch/status` - Get current watch subscription status
  - Returns: Subscription details, expiration time, active status
  - **Related Tasks:** Check if monitoring is enabled

- `GET /api/v1/gmail/messages` - List Gmail messages with filters
  - Query params: `query` (Gmail search syntax), `max_results` (default: 20)
  - Examples: "is:unread", "from:user@example.com", "subject:meeting"
  - **Related Tasks:** Browse Gmail inbox from app

- `GET /api/v1/gmail/messages/{message_id}` - Get full message details
  - Returns: Complete email with headers, body, attachments
  - **Related Tasks:** View email content

- `POST /api/v1/gmail/messages/send` - Send email via Gmail
  - Body: `{"to": "recipient@example.com", "subject": "...", "body": "...", "thread_id": "optional"}`
  - **Related Tasks:** Send emails, reply to threads

**Email Management:**
- `GET /api/v1/emails` - List user's processed emails with AI analysis
  - Query params: `skip`, `limit`, `classification` (filter by type)
  - Returns: Paginated list with email details and AI classification

- `GET /api/v1/emails/{email_id}` - Get full email details including classification
  - Returns: Complete email with body, attachments, AI analysis

**Draft Reply Management:**
- `GET /api/v1/drafts` - List pending/approved/rejected drafts (filterable by status)
  - Query params: `skip`, `limit`, `status` (pending/approved/rejected/edited)
  - Returns: Drafts with associated email context
  - **Related Tasks:** Review AI-generated drafts, track approval workflow

- `GET /api/v1/drafts/{draft_id}` - Get specific draft with email context
  - Returns: Draft content, original email, confidence score
  - **Related Tasks:** Review individual draft before approval

- `POST /api/v1/drafts/{draft_id}/approve` - Approve and send draft (optionally edit before sending)
  - Body: `{"edited_content": "optional edited text", "send_immediately": true}`
  - **Related Tasks:** Approve draft, optionally edit, send email via Gmail
  - Status changes to APPROVED or EDITED

- `POST /api/v1/drafts/{draft_id}/reject` - Reject draft with reason
  - Body: `{"rejection_reason": "Not appropriate tone"}`
  - **Related Tasks:** Reject low-quality drafts, provide feedback
  - Status changes to REJECTED

- `PUT /api/v1/drafts/{draft_id}/edit` - Edit draft content (changes status to EDITED)
  - Body: `{"draft_content": "updated text"}`
  - **Related Tasks:** Manually improve AI-generated content

**Calendar Management:**
- `GET /api/v1/calendar/events` - List user's calendar events
  - Query params: `skip`, `limit`, `created_from_email` (filter auto-created)
  - Returns: All calendar events with sync status
  - **Related Tasks:** View all scheduled meetings

- `GET /api/v1/calendar/events/upcoming` - Get upcoming events in next N days
  - Query params: `days` (default: 7)
  - Returns: Events sorted by start_time
  - **Related Tasks:** Dashboard view, daily agenda

- `POST /api/v1/calendar/events` - Manually create calendar event
  - Body: Event details (title, start_time, end_time, etc.)
  - **Related Tasks:** Manual event creation, sync to Google Calendar

- `GET /api/v1/calendar/events/{event_id}` - Get specific event details
  - Returns: Full event with attendees, location, Google Calendar sync info

**Notification Management:**
- `GET /api/v1/notifications/preferences` - Get user's notification preferences
  - Returns: All preference settings
  - **Related Tasks:** Display user settings in frontend

- `PUT /api/v1/notifications/preferences` - Update notification preferences
  - Body: Updated preference values
  - **Related Tasks:** User settings page, toggle notifications

- `POST /api/v1/notifications/subscribe` - Subscribe to push notifications (web push)
  - Body: Push subscription object (endpoint, keys)
  - **Related Tasks:** Browser push notification registration

- `GET /api/v1/notifications/subscriptions` - List active push subscriptions
  - Returns: All devices subscribed to push notifications
  - **Related Tasks:** Manage devices, view active subscriptions

**Webhooks:**
- `POST /api/v1/webhooks/gmail` - Gmail push notification webhook (Pub/Sub)
  - Body: Pub/Sub message with base64-encoded data
  - **Related Tasks:** Receive real-time Gmail notifications, trigger background processing
  - Not called directly by users - called by Google Cloud Pub/Sub

### Database Models

**EmailMessage** (`src/app/models/email_message.py`):
- Stores all processed emails with AI analysis
- Fields: message_id, thread_id, subject, from_email, body_text, body_html
- AI fields: classification, ai_analysis, confidence_score
- Timestamps: received_at, processed_at

**DraftReply** (`src/app/models/draft_reply.py`):
- AI-generated email replies pending user approval
- Status: PENDING, APPROVED, REJECTED, EDITED
- Fields: draft_content, original_draft, ai_model_used, confidence_score
- Tracks: reviewed_at, sent_at, rejection_reason

**CalendarEvent** (`src/app/models/calendar_event.py`):
- Events created from emails or manually
- Google Calendar sync: google_event_id, calendar_id, synced_at
- Fields: title, description, location, start_time, end_time, timezone
- Notification tracking: notification_sent, notification_sent_at

**NotificationPreference** (`src/app/models/notification_preference.py`):
- User preferences for notifications
- Email/push notification toggles
- Event reminder timings (15min, 1hr, 1day before)
- Auto-approval settings: auto_approve_high_confidence, confidence_threshold

**GmailWatchSubscription** (`src/app/models/gmail_watch_subscription.py`):
- Tracks Gmail push notification subscriptions
- Fields: history_id, expiration, topic_name, is_active
- Renewal tracking: last_renewed_at, renewal_failures

**PushSubscription** (`src/app/models/push_subscription.py`):
- Web push notification subscriptions (per device)
- Fields: endpoint, p256dh_key, auth_key, user_agent, device_name
- Status: is_active, last_used_at, failure_count

### Background Tasks (Celery)

**Setup Celery Worker:**
```bash
# Start Celery worker
celery -A src.app.core.celery_app worker --loglevel=info

# Start Celery beat (periodic tasks)
celery -A src.app.core.celery_app beat --loglevel=info
```

**Tasks:**

1. **process_new_emails_task** - Triggered by Gmail webhook
   - Fetches new emails from Gmail history
   - Processes each email through AI pipeline
   - Creates drafts and calendar events as needed

2. **check_upcoming_events** - Runs every minute
   - Checks for events in next 24 hours
   - Sends push notifications based on user preferences
   - Respects notification timing settings (15min, 1hr, 1day before)

3. **renew_gmail_watch_subscriptions** - Runs daily
   - Renews Gmail watch subscriptions expiring in next 2 days
   - Prevents service disruption from expired subscriptions
   - Tracks renewal failures (deactivates after 3 failures)

### Google Cloud Pub/Sub Setup

**Required Setup:**

1. Create Pub/Sub topic:
```bash
gcloud pubsub topics create gmail-notifications
```

2. Create push subscription:
```bash
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-notifications \
  --push-endpoint=https://your-domain.com/api/v1/webhooks/gmail
```

3. Grant Gmail permission to publish:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

4. Add to `src/.env`:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
PUBSUB_TOPIC_NAME=gmail-notifications
```

### Web Push Notifications Setup

**Generate VAPID Keys:**
```bash
# Install web-push CLI (npm)
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys
```

**Add to `src/.env`:**
```env
VAPID_SUBJECT=mailto:your-email@example.com
VAPID_PUBLIC_KEY=your_public_key
VAPID_PRIVATE_KEY=your_private_key
```

**Frontend Integration:**
```javascript
// Request push notification permission
const registration = await navigator.serviceWorker.register('/sw.js');
const permission = await Notification.requestPermission();

if (permission === 'granted') {
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: 'YOUR_VAPID_PUBLIC_KEY'
  });

  // Send subscription to backend
  await fetch('/api/v1/notifications/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription)
  });
}
```

### AI Configuration

**Environment Variables:**
```env
# AI Provider (claude or openai)
AI_PROVIDER=claude

# API Keys
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Models
AI_MODEL_CLASSIFICATION=claude-3-haiku-20240307
AI_MODEL_REPLY=claude-3-5-sonnet-20241022

# Thresholds
AI_CONFIDENCE_THRESHOLD=0.8

# Features
AUTO_CREATE_CALENDAR_EVENTS=true
REQUIRE_EVENT_CONFIRMATION=false

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### Complete Workflow Example

**1. User Receives Email About Meeting:**
- Gmail receives email with subject "Team Meeting Next Tuesday at 2pm"
- Gmail sends push notification to Pub/Sub topic
- Webhook receives notification with history_id
- Celery task `process_new_emails_task` is queued

**2. Background Processing:**
- Task fetches email from Gmail API
- Stores email in `email_message` table
- AIService classifies email as `CALENDAR_PLANNING` (confidence: 0.92)
- AIService extracts event details: title, start_time, end_time, location
- CalendarEventExtractor creates event in Google Calendar
- Event stored in `calendar_event` table
- NotificationService sends push notification: "Calendar event created: Team Meeting"

**3. User Receives Email Requiring Reply:**
- Email classified as `REQUIRES_REPLY` (confidence: 0.87)
- AIService generates draft reply based on email context
- Draft stored in `draft_reply` table with status=PENDING
- NotificationService sends push notification: "New draft reply needs your review"
- User opens app, reviews draft, edits slightly, approves
- Draft status changes to EDITED, sent via Gmail API

**4. Upcoming Event Notification:**
- Celery beat runs `check_upcoming_events` every minute
- Finds event starting in 15 minutes
- Checks user's notification preferences (notify_15_min_before=true)
- NotificationService sends push: "Team Meeting starts in 15 minutes"
- Event marked as notification_sent=true

### Future Endpoint Ideas

- `/api/v1/gmail/search` - Advanced email search with filters
- `/api/v1/gmail/send` - Send emails with attachments
- `/api/v1/calendar/free-slots` - Find available meeting times
- `/api/v1/calendar/schedule` - AI-powered meeting scheduling
- `/api/v1/ai/summarize-emails` - Summarize unread emails
- `/api/v1/ai/suggest-replies` - Generate email reply suggestions
