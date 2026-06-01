"""
GTU-ITR R&D & IIC Portal - AI Report Generator
Queries all database models for a given period and uses the AI engine
to produce a narrative summary report.
"""

import logging
from datetime import date

from extensions import db
from services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Report prompt
# ---------------------------------------------------------------------------

_REPORT_PROMPT = """\
You are a report-writing assistant for the Gujarat Technological University
Innovation & Incubation Cell (GTU-ITR IIC).

Based on the following data summary for the period {period_start} to {period_end},
generate a comprehensive, well-structured narrative report suitable for
submission to university management.

The report should include:
1. Executive Summary
2. Research Schemes & Grants
3. Research Proposals
4. Publications & Patents
5. IIC Events & Activities
6. Key Achievements & Highlights
7. Recommendations for Next Period

DATA SUMMARY:
{data_summary}

Write the report in a formal, professional tone. Use numbered sections and
bullet points where appropriate. Be specific with numbers and names.
"""


class ReportGenerator:
    """
    Collects data across all portal models for a date range and uses the
    AI engine to generate a narrative report.

    Usage::

        from datetime import date
        report_text = ReportGenerator.generate(
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
        )
    """

    @classmethod
    def generate(cls, period_start: date, period_end: date) -> str | None:
        """
        Generate a narrative report covering *period_start* to *period_end*.

        Returns the report text, or ``None`` on failure.
        Must be called within a Flask application context (for DB access).
        """
        try:
            data_summary = cls._collect_data(period_start, period_end)

            prompt = _REPORT_PROMPT.format(
                period_start=period_start.strftime('%d %B %Y'),
                period_end=period_end.strftime('%d %B %Y'),
                data_summary=data_summary,
            )

            report = AIEngine.generate(
                prompt,
                temperature=0.5,
                top_p=0.9,
                max_new_tokens=2048,
            )

            if report is None:
                logger.error("AI engine returned None for report.")
                return None

            return report

        except Exception as exc:
            logger.exception("ReportGenerator.generate failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    @classmethod
    def _collect_data(cls, start: date, end: date) -> str:
        """
        Query all models and build a text summary of activity in the period.
        """
        from models.scheme import Scheme
        from models.proposal import Proposal
        from models.publication import Publication
        from models.event import Event

        sections: list[str] = []

        # --- Schemes ---
        schemes = Scheme.query.filter(
            Scheme.created_at >= start,
            Scheme.created_at <= end,
        ).all()
        sections.append(cls._summarise_schemes(schemes))

        # --- Proposals ---
        proposals = Proposal.query.filter(
            Proposal.created_at >= start,
            Proposal.created_at <= end,
        ).all()
        sections.append(cls._summarise_proposals(proposals))

        # --- Publications ---
        publications = Publication.query.filter(
            Publication.created_at >= start,
            Publication.created_at <= end,
        ).all()
        sections.append(cls._summarise_publications(publications))

        # --- Events ---
        events = Event.query.filter(
            Event.date >= start,
            Event.date <= end,
        ).all()
        sections.append(cls._summarise_events(events))

        return '\n\n'.join(sections)

    # ------------------------------------------------------------------
    # Section summarisers
    # ------------------------------------------------------------------

    @staticmethod
    def _summarise_schemes(schemes) -> str:
        lines = [f"SCHEMES & GRANTS ({len(schemes)} total):"]
        if not schemes:
            lines.append("  No new schemes recorded in this period.")
        for s in schemes:
            lines.append(
                f"  - {s.title} | Agency: {s.funding_agency or 'N/A'} | "
                f"Category: {s.category} | Status: {s.status} | "
                f"Amount: {s.funding_amount or 'N/A'} | "
                f"Deadline: {s.deadline or 'N/A'}"
            )
        return '\n'.join(lines)

    @staticmethod
    def _summarise_proposals(proposals) -> str:
        lines = [f"PROPOSALS ({len(proposals)} total):"]
        if not proposals:
            lines.append("  No proposals submitted in this period.")
        status_counts: dict[str, int] = {}
        for p in proposals:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1
            lines.append(
                f"  - {p.title} | Faculty: {p.faculty.full_name if p.faculty else 'N/A'} | "
                f"Dept: {p.department.name if p.department else 'N/A'} | "
                f"Status: {p.status} | Budget: {p.budget_amount or 'N/A'}"
            )
        if status_counts:
            summary = ', '.join(f"{k}: {v}" for k, v in status_counts.items())
            lines.append(f"  Status breakdown: {summary}")
        return '\n'.join(lines)

    @staticmethod
    def _summarise_publications(publications) -> str:
        lines = [f"PUBLICATIONS & PATENTS ({len(publications)} total):"]
        if not publications:
            lines.append("  No publications recorded in this period.")
        type_counts: dict[str, int] = {}
        for pub in publications:
            type_counts[pub.pub_type] = type_counts.get(pub.pub_type, 0) + 1
            lines.append(
                f"  - {pub.title} | Type: {pub.pub_type} | "
                f"Authors: {pub.authors} | "
                f"Journal: {pub.journal or 'N/A'} | "
                f"Impact Factor: {pub.impact_factor or 'N/A'}"
            )
        if type_counts:
            summary = ', '.join(f"{k}: {v}" for k, v in type_counts.items())
            lines.append(f"  Type breakdown: {summary}")
        return '\n'.join(lines)

    @staticmethod
    def _summarise_events(events) -> str:
        lines = [f"IIC EVENTS & ACTIVITIES ({len(events)} total):"]
        if not events:
            lines.append("  No events conducted in this period.")
        total_participants = 0
        for e in events:
            total_participants += e.participants_count or 0
            lines.append(
                f"  - {e.title} | Type: {e.event_type} | "
                f"Date: {e.date} | Venue: {e.venue or 'N/A'} | "
                f"Participants: {e.participants_count or 0} | "
                f"Status: {e.status}"
            )
        lines.append(f"  Total participants across all events: {total_participants}")
        return '\n'.join(lines)
