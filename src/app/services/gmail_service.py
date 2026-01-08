"""Gmail API service for reading and sending emails."""

from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GmailService:
    """Service for interacting with Gmail API."""

    def __init__(self, access_token: str):
        """Initialize Gmail service with OAuth2 credentials.

        Parameters
        ----------
        access_token: str
            Valid Google OAuth2 access token
        """
        self.credentials = Credentials(token=access_token)
        self.service = build("gmail", "v1", credentials=self.credentials)

    async def list_messages(
        self, query: str = "", max_results: int = 10, label_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """List Gmail messages matching query.

        Parameters
        ----------
        query: str
            Gmail search query (e.g., "is:unread", "from:example@gmail.com")
        max_results: int
            Maximum number of messages to return
        label_ids: list[str] | None
            Filter by label IDs (e.g., ["INBOX", "UNREAD"])

        Returns
        -------
        list[dict[str, Any]]
            List of message objects
        """
        request_params: dict[str, Any] = {"userId": "me", "maxResults": max_results}

        if query:
            request_params["q"] = query
        if label_ids:
            request_params["labelIds"] = label_ids

        results = self.service.users().messages().list(**request_params).execute()
        messages = results.get("messages", [])

        # Get full message details for each message
        full_messages = []
        for message in messages:
            msg = self.service.users().messages().get(userId="me", id=message["id"]).execute()
            full_messages.append(msg)

        return full_messages

    async def get_message(self, message_id: str) -> dict[str, Any]:
        """Get a specific Gmail message by ID.

        Parameters
        ----------
        message_id: str
            Gmail message ID

        Returns
        -------
        dict[str, Any]
            Message object with headers, body, etc.
        """
        message = self.service.users().messages().get(userId="me", id=message_id).execute()
        return message

    async def send_message(
        self, to: str, subject: str, body: str, from_email: str | None = None, thread_id: str | None = None
    ) -> dict[str, Any]:
        """Send an email via Gmail.

        Parameters
        ----------
        to: str
            Recipient email address
        subject: str
            Email subject
        body: str
            Email body (plain text)
        from_email: str | None
            Sender email (optional, defaults to authenticated user)
        thread_id: str | None
            Thread ID to reply to (optional)

        Returns
        -------
        dict[str, Any]
            Sent message object
        """
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if from_email:
            message["from"] = from_email

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {"raw": raw_message}
        if thread_id:
            send_message["threadId"] = thread_id

        sent = self.service.users().messages().send(userId="me", body=send_message).execute()
        return sent

    async def get_labels(self) -> list[dict[str, Any]]:
        """Get all Gmail labels for the user.

        Returns
        -------
        list[dict[str, Any]]
            List of label objects
        """
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        return labels

    async def mark_as_read(self, message_id: str) -> dict[str, Any]:
        """Mark a message as read.

        Parameters
        ----------
        message_id: str
            Gmail message ID

        Returns
        -------
        dict[str, Any]
            Updated message object
        """
        message = (
            self.service.users()
            .messages()
            .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )
        return message

    async def mark_as_unread(self, message_id: str) -> dict[str, Any]:
        """Mark a message as unread.

        Parameters
        ----------
        message_id: str
            Gmail message ID

        Returns
        -------
        dict[str, Any]
            Updated message object
        """
        message = (
            self.service.users()
            .messages()
            .modify(userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]})
            .execute()
        )
        return message

    async def delete_message(self, message_id: str) -> None:
        """Delete a message (move to trash).

        Parameters
        ----------
        message_id: str
            Gmail message ID
        """
        self.service.users().messages().trash(userId="me", id=message_id).execute()

    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Get an entire email thread.

        Parameters
        ----------
        thread_id: str
            Gmail thread ID

        Returns
        -------
        dict[str, Any]
            Thread object containing all messages
        """
        thread = self.service.users().threads().get(userId="me", id=thread_id).execute()
        return thread

    async def setup_watch(self, topic_name: str) -> dict[str, Any]:
        """Set up Gmail push notifications via Pub/Sub.

        Parameters
        ----------
        topic_name: str
            Full topic name: projects/{project}/topics/{topic}

        Returns
        -------
        dict[str, Any]
            Watch response with historyId and expiration
        """
        request_body = {"topicName": topic_name, "labelIds": ["INBOX"]}

        watch_response = self.service.users().watch(userId="me", body=request_body).execute()
        return watch_response

    async def stop_watch(self) -> None:
        """Stop Gmail push notifications."""
        self.service.users().stop(userId="me").execute()

    async def get_history(self, start_history_id: int) -> list[dict[str, Any]]:
        """Get message history since a specific history ID.

        Parameters
        ----------
        start_history_id: int
            History ID to start from

        Returns
        -------
        list[dict[str, Any]]
            List of history records
        """
        try:
            history = (
                self.service.users()
                .history()
                .list(userId="me", startHistoryId=start_history_id, historyTypes=["messageAdded"])
                .execute()
            )
            return history.get("history", [])
        except Exception:
            return []
