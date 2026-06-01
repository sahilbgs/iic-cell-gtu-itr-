"""
GTU-ITR R&D & IIC Portal - AI Email Drafter
Generates professional email drafts for scheme circulation, follow-ups,
and custom contexts using the AI engine.
"""

import json
import logging
import re

from services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_CIRCULATION_PROMPT = """\
You are an email drafting assistant for the Gujarat Technological University
Innovation & Incubation Cell (GTU-ITR IIC).

Draft a professional email to circulate the following funding scheme to
faculty members. The email should be formal, encouraging, and include all
key details.

Scheme details:
- Title: {title}
- Funding Agency: {funding_agency}
- Category: {category}
- Deadline: {deadline}
- Funding Amount: {funding_amount}
- Eligibility: {eligibility}
- Summary: {summary}

Return your answer as a JSON object with these keys:
{{
  "subject": "<email subject line>",
  "body": "<full email body in plain text>",
  "recipients": "<suggested recipient group, e.g. 'All Faculty', 'HODs'>"
}}

Return ONLY the JSON, no extra text.
"""

_FOLLOWUP_PROMPT = """\
You are an email drafting assistant for the Gujarat Technological University
Innovation & Incubation Cell (GTU-ITR IIC).

Draft a professional follow-up email to a faculty member regarding a funding
scheme. The tone should be polite and encouraging.

Faculty: {faculty_name} ({faculty_email})
Department: {department}
Scheme: {scheme_title}
Deadline: {deadline}
Current Status: {status}

Return your answer as a JSON object:
{{
  "subject": "<email subject line>",
  "body": "<full email body in plain text>",
  "recipients": "{faculty_email}"
}}

Return ONLY the JSON, no extra text.
"""

_CUSTOM_PROMPT = """\
You are an email drafting assistant for the Gujarat Technological University
Innovation & Incubation Cell (GTU-ITR IIC).

Draft a professional email based on the following context:

{context}

Return your answer as a JSON object:
{{
  "subject": "<email subject line>",
  "body": "<full email body in plain text>",
  "recipients": "<suggested recipients>"
}}

Return ONLY the JSON, no extra text.
"""


class EmailDrafter:
    """
    AI-powered email draft generation.

    Usage::

        email = EmailDrafter.draft_circulation_email(scheme_dict)
        print(email['subject'], email['body'])
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def draft_circulation_email(cls, scheme: dict) -> dict | None:
        """
        Generate a circulation email for a funding scheme.

        *scheme* should be a dict (or Scheme model instance attributes) with
        keys: title, funding_agency, category, deadline, funding_amount,
        eligibility, summary.

        Returns ``{"subject": …, "body": …, "recipients": …}`` or ``None``.
        """
        try:
            prompt = _CIRCULATION_PROMPT.format(
                title=scheme.get('title', 'N/A'),
                funding_agency=scheme.get('funding_agency', 'N/A'),
                category=scheme.get('category', 'N/A'),
                deadline=scheme.get('deadline', 'Not specified'),
                funding_amount=scheme.get('funding_amount', 'Not specified'),
                eligibility=scheme.get('eligibility', 'Not specified'),
                summary=scheme.get('summary', scheme.get('description', 'N/A')),
            )
            return cls._generate_and_parse(prompt)

        except Exception as exc:
            logger.exception("draft_circulation_email failed: %s", exc)
            return None

    @classmethod
    def draft_followup(cls, faculty: dict, scheme: dict) -> dict | None:
        """
        Generate a follow-up email for a faculty member about a scheme.

        *faculty* should have: full_name, email, department (name string).
        *scheme* should have: title, deadline, status.

        Returns ``{"subject": …, "body": …, "recipients": …}`` or ``None``.
        """
        try:
            prompt = _FOLLOWUP_PROMPT.format(
                faculty_name=faculty.get('full_name', 'Professor'),
                faculty_email=faculty.get('email', ''),
                department=faculty.get('department', 'N/A'),
                scheme_title=scheme.get('title', 'N/A'),
                deadline=scheme.get('deadline', 'Not specified'),
                status=scheme.get('status', 'OPEN'),
            )
            return cls._generate_and_parse(prompt)

        except Exception as exc:
            logger.exception("draft_followup failed: %s", exc)
            return None

    @classmethod
    def draft_custom(cls, context: str) -> dict | None:
        """
        Generate an email based on a free-form context description.

        Returns ``{"subject": …, "body": …, "recipients": …}`` or ``None``.
        """
        try:
            if not context or not context.strip():
                logger.warning("draft_custom called with empty context.")
                return None

            prompt = _CUSTOM_PROMPT.format(context=context)
            return cls._generate_and_parse(prompt)

        except Exception as exc:
            logger.exception("draft_custom failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _generate_and_parse(cls, prompt: str) -> dict | None:
        """Send prompt to AI engine and parse the JSON response."""
        response = AIEngine.generate(
            prompt,
            temperature=0.6,
            top_p=0.9,
        )

        if response is None:
            logger.error("AI engine returned None for email draft.")
            return None

        parsed = cls._extract_json(response)
        if parsed is None:
            # If JSON parsing fails, try to return the response as body text
            logger.warning("Could not parse JSON; using raw response as body.")
            return {
                'subject': 'GTU-ITR IIC Notification',
                'body': response,
                'recipients': 'All Faculty',
            }

        # Ensure required keys
        return {
            'subject': parsed.get('subject', 'GTU-ITR IIC Notification'),
            'body': parsed.get('body', ''),
            'recipients': parsed.get('recipients', 'All Faculty'),
        }

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """Extract a JSON object from the AI response."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except (json.JSONDecodeError, TypeError):
                    continue
        return None
