"""
GTU-ITR R&D & IIC Portal - AI Scheme Classifier
Sends raw document text to the AI engine and asks for structured JSON
describing the funding scheme.
"""

import json
import logging
import re

from services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are an expert assistant for a university Research & Development office.
Analyse the following document text describing a funding scheme or grant
opportunity, and extract the key details.

Return your answer as a single, valid JSON object with exactly these keys:

{
  "title": "<scheme/grant title>",
  "category": "<one of: GOVERNMENT, INDUSTRY, INTERNAL, INTERNATIONAL>",
  "funding_agency": "<name of the funding organisation>",
  "eligible_departments": ["<list of eligible department names>"],
  "deadline": "<deadline date in YYYY-MM-DD format, or null if not found>",
  "funding_amount": <numeric amount in INR, or null if not found>,
  "priority": "<one of: HIGH, MEDIUM, LOW>",
  "eligibility": "<eligibility criteria summary>",
  "summary": "<concise 2-3 sentence summary of the scheme>"
}

Rules:
- Return ONLY the JSON object, no additional text or markdown fencing.
- If a field cannot be determined, use null for scalar fields or [] for lists.
- The category MUST be one of GOVERNMENT, INDUSTRY, INTERNAL, INTERNATIONAL.
- The priority MUST be one of HIGH, MEDIUM, LOW.
"""


class SchemeClassifier:
    """
    Extracts structured scheme metadata from raw document text using the
    AI engine.

    Usage::

        result = SchemeClassifier.classify(raw_text)
        if result:
            print(result['title'], result['category'])
    """

    # Expected keys for validation
    _EXPECTED_KEYS = {
        'title', 'category', 'funding_agency', 'eligible_departments',
        'deadline', 'funding_amount', 'priority', 'eligibility', 'summary',
    }

    _VALID_CATEGORIES = {'GOVERNMENT', 'INDUSTRY', 'INTERNAL', 'INTERNATIONAL'}
    _VALID_PRIORITIES = {'HIGH', 'MEDIUM', 'LOW'}

    @classmethod
    def classify(cls, raw_text: str) -> dict | None:
        """
        Analyse *raw_text* and return a dict of scheme fields,
        or ``None`` on failure.
        """
        try:
            if not raw_text or not raw_text.strip():
                logger.warning("classify() called with empty text.")
                return None

            # Truncate very long documents to stay within context window
            truncated = raw_text[:12_000]

            prompt = (
                f"{_SYSTEM_PROMPT}\n\n"
                f"--- DOCUMENT TEXT ---\n{truncated}\n--- END ---\n\n"
                "JSON:"
            )

            response = AIEngine.generate(
                prompt,
                temperature=0.3,   # Low temperature for factual extraction
                top_p=0.85,
            )

            if response is None:
                logger.error("AI engine returned None.")
                return None

            parsed = cls._extract_json(response)
            if parsed is None:
                logger.error("Could not parse JSON from AI response.")
                return None

            # Normalise / validate
            parsed = cls._normalise(parsed)
            return parsed

        except Exception as exc:
            logger.exception("SchemeClassifier.classify failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # JSON extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """
        Attempt to pull a JSON object out of the AI response.
        Handles cases where the model wraps it in markdown fences.
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find a JSON block inside ```json ... ``` or { ... }
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

    @classmethod
    def _normalise(cls, data: dict) -> dict:
        """Ensure the returned dict has all expected keys with valid values."""
        result = {}
        for key in cls._EXPECTED_KEYS:
            result[key] = data.get(key)

        # Enforce enum values
        if result.get('category') not in cls._VALID_CATEGORIES:
            result['category'] = 'GOVERNMENT'  # default

        if result.get('priority') not in cls._VALID_PRIORITIES:
            result['priority'] = 'MEDIUM'  # default

        # Ensure eligible_departments is a list
        if not isinstance(result.get('eligible_departments'), list):
            result['eligible_departments'] = []

        # Ensure funding_amount is numeric or None
        if result.get('funding_amount') is not None:
            try:
                result['funding_amount'] = float(result['funding_amount'])
            except (ValueError, TypeError):
                result['funding_amount'] = None

        return result
