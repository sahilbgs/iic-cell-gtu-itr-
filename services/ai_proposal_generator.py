"""
GTU-ITR R&D & IIC Portal - AI Proposal Generator
Generates full research proposal drafts using the AI engine.
"""

import json
import logging
import re

from services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROPOSAL_PROMPT = """\
You are an expert research proposal writer for Gujarat Technological University.
Generate a comprehensive research proposal based on the following inputs.

Topic / Research Area: {topic}
Department: {department}
Funding Agency: {funding_agency}
Principal Investigator: {faculty_name}

Generate a full research proposal and return it as a JSON object with these keys:

{{
  "title": "<formal research proposal title>",
  "objectives": "<numbered list of 4-5 specific, measurable research objectives>",
  "methodology": "<detailed methodology in 3-4 paragraphs covering approach, tools, techniques, and validation>",
  "timeline": "<project timeline broken into phases with milestones, e.g. Phase 1 (Month 1-3): ...>",
  "budget": "<itemised budget breakdown with categories: equipment, consumables, travel, manpower, contingency, and total>",
  "expected_outcomes": "<4-5 expected outcomes including publications, patents, prototypes, societal impact>"
}}

Guidelines:
- Be specific and technical, suitable for a formal grant application.
- Budget should be realistic for an Indian academic research project.
- Timeline should span 2-3 years.
- Reference relevant Indian funding norms where applicable.
- Return ONLY the JSON object, no extra text.
"""


class ProposalGenerator:
    """
    AI-powered research proposal generation.

    Usage::

        proposal = ProposalGenerator.generate(
            topic="IoT-based Smart Agriculture",
            department="Computer Engineering",
            funding_agency="DST-SERB",
            faculty_name="Dr. Amit Patel",
        )
        if proposal:
            print(proposal['title'])
            print(proposal['methodology'])
    """

    _EXPECTED_KEYS = {
        'title', 'objectives', 'methodology',
        'timeline', 'budget', 'expected_outcomes',
    }

    @classmethod
    def generate(
        cls,
        topic: str,
        department: str,
        funding_agency: str = "Not specified",
        faculty_name: str = "Not specified",
    ) -> dict | None:
        """
        Generate a research proposal for the given *topic*.

        Returns a dict with keys: title, objectives, methodology, timeline,
        budget, expected_outcomes — or ``None`` on failure.
        """
        try:
            if not topic or not topic.strip():
                logger.warning("generate() called with empty topic.")
                return None

            prompt = _PROPOSAL_PROMPT.format(
                topic=topic,
                department=department or "Not specified",
                funding_agency=funding_agency or "Not specified",
                faculty_name=faculty_name or "Not specified",
            )

            response = AIEngine.generate(
                prompt,
                temperature=0.7,
                top_p=0.9,
                max_new_tokens=2048,
            )

            if response is None:
                logger.error("AI engine returned None for proposal.")
                return None

            parsed = cls._extract_json(response)

            if parsed is None:
                # Try to build a structured response from free text
                logger.warning("JSON parse failed; returning raw text as proposal body.")
                return {
                    'title': f"Research Proposal: {topic}",
                    'objectives': response,
                    'methodology': '',
                    'timeline': '',
                    'budget': '',
                    'expected_outcomes': '',
                }

            # Ensure all keys present
            result = {}
            for key in cls._EXPECTED_KEYS:
                result[key] = parsed.get(key, '')

            return result

        except Exception as exc:
            logger.exception("ProposalGenerator.generate failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

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
