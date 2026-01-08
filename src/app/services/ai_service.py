"""AI service for email classification, reply generation, and calendar extraction."""

import json
from typing import Any

from anthropic import Anthropic
from openai import OpenAI

from ..core.config import settings
from ..models.email_message import EmailClassification


class AIService:
    """Service for AI operations using Claude or OpenAI."""

    def __init__(self):
        """Initialize AI service with configured provider."""
        self.provider = settings.AI_PROVIDER

        if self.provider == "claude":
            if not settings.CLAUDE_API_KEY.get_secret_value():
                raise ValueError("CLAUDE_API_KEY is not configured")
            self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY.get_secret_value())
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY.get_secret_value():
                raise ValueError("OPENAI_API_KEY is not configured")
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
        else:
            raise ValueError(f"Invalid AI_PROVIDER: {self.provider}")

    async def classify_email(self, subject: str, body: str, from_email: str) -> dict[str, Any]:
        """Classify an email into categories.

        Parameters
        ----------
        subject: str
            Email subject
        body: str
            Email body text
        from_email: str
            Sender email address

        Returns
        -------
        dict[str, Any]
            Classification result with keys: classification, confidence_score, reasoning
        """
        prompt = f"""Analyze this email and classify it into one of these categories:
- CALENDAR_PLANNING: Contains meeting invites, scheduling requests, or event planning
- REQUIRES_REPLY: Questions, requests, or messages that need a response
- INFORMATIONAL: Newsletters, updates, notifications that don't need action
- SPAM: Unsolicited or promotional emails
- OTHER: Doesn't fit other categories

Email Details:
From: {from_email}
Subject: {subject}
Body: {body[:1000]}

Respond in JSON format with:
{{
    "classification": "CATEGORY_NAME",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        if self.provider == "claude":
            response = self.claude_client.messages.create(
                model=settings.AI_MODEL_CLASSIFICATION,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            result_text = response.content[0].text
        else:
            response = self.openai_client.chat.completions.create(
                model=settings.AI_MODEL_CLASSIFICATION,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content

        try:
            result = json.loads(result_text)
            # Validate classification
            if result["classification"] not in [e.value for e in EmailClassification]:
                result["classification"] = EmailClassification.OTHER.value
            return result
        except (json.JSONDecodeError, KeyError):
            return {
                "classification": EmailClassification.OTHER.value,
                "confidence_score": 0.5,
                "reasoning": "Failed to parse AI response",
            }

    async def generate_reply(
        self, subject: str, body: str, from_email: str, thread_context: str | None = None
    ) -> dict[str, Any]:
        """Generate a draft email reply.

        Parameters
        ----------
        subject: str
            Original email subject
        body: str
            Original email body
        from_email: str
            Sender email address
        thread_context: str | None
            Previous messages in thread (optional)

        Returns
        -------
        dict[str, Any]
            Draft reply with keys: content, confidence_score, reasoning
        """
        thread_info = f"\n\nPrevious Context:\n{thread_context}" if thread_context else ""

        prompt = f"""You are a professional email assistant. Generate a polite, concise reply to this email.

Original Email:
From: {from_email}
Subject: {subject}
Body: {body}{thread_info}

Requirements:
- Be professional and courteous
- Match the tone of the original email
- Address all questions or requests
- Keep it concise (2-4 paragraphs max)
- Don't include signature (will be added automatically)

Respond in JSON format with:
{{
    "content": "draft reply text",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation of approach"
}}"""

        if self.provider == "claude":
            response = self.claude_client.messages.create(
                model=settings.AI_MODEL_REPLY, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.content[0].text
        else:
            response = self.openai_client.chat.completions.create(
                model=settings.AI_MODEL_REPLY,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content

        try:
            result = json.loads(result_text)
            return result
        except (json.JSONDecodeError, KeyError):
            return {"content": "", "confidence_score": 0.0, "reasoning": "Failed to parse AI response"}

    async def extract_calendar_event(self, subject: str, body: str) -> dict[str, Any] | None:
        """Extract calendar event details from email.

        Parameters
        ----------
        subject: str
            Email subject
        body: str
            Email body text

        Returns
        -------
        dict[str, Any] | None
            Extracted event details or None if no event found
            Keys: title, description, location, start_time, end_time, attendees, confidence_score, reasoning
        """
        prompt = f"""Extract calendar event details from this email. If no clear event is present, return null.

Email Subject: {subject}
Email Body: {body}

If an event is found, respond in JSON format with:
{{
    "title": "event title",
    "description": "event description",
    "location": "physical or virtual location (or null)",
    "start_time": "ISO 8601 datetime",
    "end_time": "ISO 8601 datetime",
    "timezone": "timezone name",
    "attendees": ["email1@example.com", "email2@example.com"],
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}

If NO event found, respond with: {{"event_found": false}}

Important:
- Parse natural language dates like "next Tuesday at 3pm", "tomorrow at 10am"
- Assume current year if not specified
- Default to 1-hour duration if end time not specified
- Extract all mentioned attendees"""

        if self.provider == "claude":
            response = self.claude_client.messages.create(
                model=settings.AI_MODEL_CALENDAR, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.content[0].text
        else:
            response = self.openai_client.chat.completions.create(
                model=settings.AI_MODEL_CALENDAR,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content

        try:
            result = json.loads(result_text)
            if result.get("event_found") is False:
                return None
            return result
        except (json.JSONDecodeError, KeyError):
            return None
