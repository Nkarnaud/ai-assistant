# AI Email Assistant

An intelligent email management system that uses AI to automatically process Gmail messages, extract calendar events, generate draft replies, and send push notifications.

## Features

### 🤖 AI-Powered Email Processing
- **Automatic Classification**: Claude/OpenAI models classify emails (calendar planning, requires reply, informational, spam)
- **Smart Reply Generation**: AI generates contextual draft replies for user approval
- **Event Extraction**: Automatically extracts meeting details from emails and creates calendar events

### 📧 Gmail Integration
- **Real-time Monitoring**: Gmail push notifications via Google Pub/Sub
- **Full Gmail API**: Send, receive, search, and manage emails
- **Thread Support**: Reply to email threads with context

### 📅 Calendar Management
- **Auto-Create Events**: Automatically creates Google Calendar events from meeting emails
- **Confidence Thresholds**: Configurable confidence scores for auto-creation
- **Sync Status**: Track sync status and event updates

### 🔔 Smart Notifications
- **Web Push Notifications**: Browser notifications for drafts, events, and updates
- **Customizable Preferences**: Configure notification timings (15min, 1hr, 1day before events)
- **Multi-Device Support**: Push to all user's subscribed devices

### 🛠️ Production-Ready Architecture
- **FastAPI**: Fully async Python web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Celery + Redis**: Background task processing and caching
- **PostgreSQL**: Robust relational database
- **Docker**: One-command containerized deployment

## Tech Stack

- **Framework**: FastAPI with Pydantic v2
- **Database**: PostgreSQL 13 with SQLAlchemy 2.0
- **Cache/Queue**: Redis (caching + Celery broker)
- **Background Tasks**: Celery with Celery Beat
- **AI Models**: Claude (Anthropic) + OpenAI GPT
- **Google APIs**: Gmail API, Calendar API, Cloud Pub/Sub
- **Authentication**: JWT + OAuth2 (Google)
- **Container**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Google Cloud Project with Gmail API and Calendar API enabled
- OAuth 2.0 Client credentials
- Claude API key or OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ai-assistant
```

2. **Run setup script**
```bash
./setup.py local  # or staging/production
```

This will copy the appropriate Docker configuration and create `src/.env` file.

3. **Configure environment variables** in `src/.env`:
```env
# App Settings
APP_NAME=AI Email Assistant
ENVIRONMENT=local

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=ai_assistant

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_CACHE_HOST=redis
REDIS_CACHE_PORT=6379

# Google OAuth2
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# Google Cloud Pub/Sub
GOOGLE_CLOUD_PROJECT=your-project-id
PUBSUB_TOPIC_NAME=gmail-notifications

# Token Encryption
TOKEN_ENCRYPTION_KEY=your-fernet-key

# AI Configuration
AI_PROVIDER=claude  # or openai
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
AI_MODEL_CLASSIFICATION=claude-3-haiku-20240307
AI_MODEL_REPLY=claude-3-5-sonnet-20241022
AI_CONFIDENCE_THRESHOLD=0.8

# Features
AUTO_CREATE_CALENDAR_EVENTS=true
REQUIRE_EVENT_CONFIRMATION=false

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Web Push (optional)
VAPID_SUBJECT=mailto:your-email@example.com
VAPID_PUBLIC_KEY=your_public_key
VAPID_PRIVATE_KEY=your_private_key
```

4. **Generate encryption key**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

5. **Start the application**
```bash
docker compose up
```

6. **Create superuser**
```bash
docker compose run --rm create_superuser
```

7. **Run migrations**
```bash
docker compose exec web bash -c "cd /app && alembic upgrade head"
```

### Access the Application

- **API Docs**: http://127.0.0.1:8000/docs
- **API**: http://127.0.0.1:8000/api/v1/

## Google Cloud Setup

### 1. Enable APIs
```bash
gcloud services enable gmail.googleapis.com
gcloud services enable calendar-json.googleapis.com
gcloud services enable pubsub.googleapis.com
```

### 2. Create Pub/Sub Topic
```bash
gcloud pubsub topics create gmail-notifications
```

### 3. Create Push Subscription
```bash
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-notifications \
  --push-endpoint=https://your-domain.com/api/v1/webhooks/gmail
```

### 4. Grant Gmail Permissions
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## Usage

### 1. Connect Google Account

Navigate to `/api/v1/auth/google` to start OAuth flow and grant Gmail/Calendar permissions.

### 2. Enable Gmail Watch

```bash
curl -X POST http://127.0.0.1:8000/api/v1/gmail/watch/setup \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. System Workflow

**When an email arrives:**
1. Gmail sends push notification to Pub/Sub
2. Webhook triggers background Celery task
3. Email is fetched and stored in database
4. AI classifies the email:
   - **Calendar Planning**: Extracts event details → Creates in Google Calendar → Sends notification
   - **Requires Reply**: Generates draft reply → Stores for approval → Sends notification
   - **Informational**: Marks as processed

**Draft Approval:**
1. User receives push notification about new draft
2. User reviews draft at `/api/v1/drafts`
3. User approves, rejects, or edits draft
4. Approved drafts are sent via Gmail API

**Event Notifications:**
1. Celery Beat checks for upcoming events every minute
2. Sends notifications based on user preferences (15min, 1hr, 1day before)
3. Marks events as notified

## API Endpoints

### Gmail Operations
- `POST /api/v1/gmail/watch/setup` - Enable real-time email monitoring
- `POST /api/v1/gmail/watch/stop` - Disable monitoring
- `GET /api/v1/gmail/watch/status` - Check subscription status
- `GET /api/v1/gmail/messages` - List messages with filters
- `GET /api/v1/gmail/messages/{id}` - Get message details
- `POST /api/v1/gmail/messages/send` - Send email

### Email Management
- `GET /api/v1/emails` - List processed emails with AI analysis
- `GET /api/v1/emails/{id}` - Get email details

### Draft Management
- `GET /api/v1/drafts` - List pending drafts
- `GET /api/v1/drafts/{id}` - Get draft details
- `POST /api/v1/drafts/{id}/approve` - Approve and send draft
- `POST /api/v1/drafts/{id}/reject` - Reject draft
- `PUT /api/v1/drafts/{id}/edit` - Edit draft content

### Calendar
- `GET /api/v1/calendar/events` - List calendar events
- `GET /api/v1/calendar/events/upcoming` - Get upcoming events
- `POST /api/v1/calendar/events` - Create event manually
- `GET /api/v1/calendar/events/{id}` - Get event details

### Notifications
- `GET /api/v1/notifications/preferences` - Get preferences
- `PUT /api/v1/notifications/preferences` - Update preferences
- `POST /api/v1/notifications/subscribe` - Subscribe to push notifications
- `GET /api/v1/notifications/subscriptions` - List subscriptions

### Webhooks
- `POST /api/v1/webhooks/gmail` - Gmail push notification webhook

## Background Tasks

### Start Celery Worker
```bash
celery -A src.app.core.celery_app worker --loglevel=info
```

### Start Celery Beat (Periodic Tasks)
```bash
celery -A src.app.core.celery_app beat --loglevel=info
```

### Tasks
- **process_new_emails_task**: Processes incoming emails (triggered by webhook)
- **check_upcoming_events**: Checks for events and sends notifications (every minute)
- **renew_gmail_watch_subscriptions**: Renews expiring subscriptions (daily)

## Development

### Run Locally Without Docker
```bash
uv sync && uv run uvicorn src.app.main:app --reload
```

### Create Migration
```bash
cd src && uv run alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
cd src && uv run alembic upgrade head
```

### Run Tests
```bash
docker compose run --rm pytest
# or locally
uv run pytest ./tests
```

### Code Quality
```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Type check
uv run mypy src/
```

## Architecture

### Database Models
- **User**: User accounts with OAuth support
- **OAuthToken**: Encrypted OAuth tokens
- **EmailMessage**: Processed emails with AI analysis
- **DraftReply**: AI-generated draft replies
- **CalendarEvent**: Calendar events synced from emails
- **NotificationPreference**: User notification settings
- **GmailWatchSubscription**: Gmail push notification tracking
- **PushSubscription**: Web push subscriptions

### Services
- **AIService**: Claude/OpenAI integration for classification, reply generation, event extraction
- **GmailService**: Gmail API wrapper
- **CalendarService**: Google Calendar API wrapper
- **EmailProcessor**: Main email processing pipeline
- **CalendarEventExtractor**: Event extraction and creation
- **NotificationService**: Web push notifications

## Configuration

See `CLAUDE.md` for detailed configuration options and developer guidance.

## License

MIT

## Contact

For questions or support, please open an issue on GitHub.
