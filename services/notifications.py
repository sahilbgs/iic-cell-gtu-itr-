"""
GTU-ITR R&D & IIC Portal - Notification Service
Flask-Mail based email notifications for deadlines, scheme alerts,
proposal status updates, and monthly reminders.
"""

import logging
from datetime import datetime, timedelta

from flask import current_app
from flask_mail import Message

from extensions import db, mail

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Email notification utilities using Flask-Mail.

    All methods are classmethods and must be called within a Flask
    application context.

    Usage::

        from services.notifications import NotificationService
        NotificationService.send_scheme_notification(scheme, recipients)
    """

    # ------------------------------------------------------------------
    # Scheme deadline alert
    # ------------------------------------------------------------------

    @classmethod
    def send_deadline_alert(cls, scheme, recipients: list[str]) -> bool:
        """
        Send a deadline reminder for a scheme approaching its deadline.

        Parameters
        ----------
        scheme : Scheme model instance
        recipients : list of email addresses

        Returns True on success, False on failure.
        """
        try:
            days_left = scheme.days_until_deadline
            urgency = "URGENT" if days_left and days_left <= 3 else "Reminder"

            subject = f"[{urgency}] Deadline Alert: {scheme.title}"
            body = (
                f"Dear Faculty Member,\n\n"
                f"This is a reminder that the following funding scheme has an "
                f"approaching deadline:\n\n"
                f"Scheme: {scheme.title}\n"
                f"Funding Agency: {scheme.funding_agency or 'N/A'}\n"
                f"Category: {scheme.category_label}\n"
                f"Deadline: {scheme.deadline.strftime('%d %B %Y') if scheme.deadline else 'N/A'}\n"
                f"Days Remaining: {days_left if days_left is not None else 'N/A'}\n"
                f"Funding Amount: ₹{scheme.funding_amount:,.2f}" if scheme.funding_amount else ""
            )
            body += (
                f"\n\nPlease submit your proposals at the earliest.\n\n"
                f"For any queries, contact the R&D Coordination Cell.\n\n"
                f"Best regards,\n"
                f"GTU-ITR R&D & IIC Portal\n"
                f"(This is an automated notification)"
            )

            return cls._send(subject, body, recipients)

        except Exception as exc:
            logger.exception("send_deadline_alert failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # New scheme notification
    # ------------------------------------------------------------------

    @classmethod
    def send_scheme_notification(cls, scheme, recipients: list[str]) -> bool:
        """
        Notify faculty about a newly added funding scheme.

        Parameters
        ----------
        scheme : Scheme model instance
        recipients : list of email addresses
        """
        try:
            subject = f"[New Scheme] {scheme.title}"
            body = (
                f"Dear Faculty Member,\n\n"
                f"A new funding scheme has been added to the R&D Portal:\n\n"
                f"Title: {scheme.title}\n"
                f"Funding Agency: {scheme.funding_agency or 'N/A'}\n"
                f"Category: {scheme.category_label}\n"
                f"Deadline: {scheme.deadline.strftime('%d %B %Y') if scheme.deadline else 'Not specified'}\n"
                f"Priority: {scheme.priority_label}\n"
            )

            if scheme.funding_amount:
                body += f"Funding Amount: ₹{scheme.funding_amount:,.2f}\n"

            if scheme.eligibility:
                body += f"\nEligibility:\n{scheme.eligibility}\n"

            if scheme.description:
                body += f"\nDescription:\n{scheme.description[:500]}\n"

            body += (
                f"\n\nPlease log in to the portal for full details and to "
                f"submit your proposal.\n\n"
                f"Best regards,\n"
                f"GTU-ITR R&D & IIC Portal\n"
                f"(This is an automated notification)"
            )

            return cls._send(subject, body, recipients)

        except Exception as exc:
            logger.exception("send_scheme_notification failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Proposal status update
    # ------------------------------------------------------------------

    @classmethod
    def send_proposal_status_update(cls, proposal, recipient_email: str) -> bool:
        """
        Notify a faculty member about their proposal's status change.

        Parameters
        ----------
        proposal : Proposal model instance
        recipient_email : faculty email address
        """
        try:
            subject = f"[Proposal Update] {proposal.title} — {proposal.status_label}"

            body = (
                f"Dear {proposal.faculty.full_name if proposal.faculty else 'Faculty Member'},\n\n"
                f"Your research proposal has been updated:\n\n"
                f"Title: {proposal.title}\n"
                f"Status: {proposal.status_label}\n"
            )

            if proposal.scheme:
                body += f"Scheme: {proposal.scheme.title}\n"

            if proposal.review_notes:
                body += f"\nReviewer Comments:\n{proposal.review_notes}\n"

            if proposal.status == 'APPROVED':
                body += (
                    "\nCongratulations! Your proposal has been approved. "
                    "Please proceed with the next steps as outlined in the portal.\n"
                )
            elif proposal.status == 'REJECTED':
                body += (
                    "\nWe encourage you to review the feedback and consider "
                    "revising your proposal for future submissions.\n"
                )

            body += (
                f"\nPlease log in to the portal for full details.\n\n"
                f"Best regards,\n"
                f"GTU-ITR R&D & IIC Portal\n"
                f"(This is an automated notification)"
            )

            return cls._send(subject, body, [recipient_email])

        except Exception as exc:
            logger.exception("send_proposal_status_update failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Monthly reminder
    # ------------------------------------------------------------------

    @classmethod
    def send_monthly_reminder(cls, recipients: list[str]) -> bool:
        """
        Send a monthly digest / reminder to all faculty with upcoming
        deadlines and pending actions.
        """
        try:
            from models.scheme import Scheme
            from models.proposal import Proposal

            now = datetime.utcnow().date()
            next_month = now + timedelta(days=30)

            # Upcoming deadlines
            upcoming_schemes = Scheme.query.filter(
                Scheme.deadline >= now,
                Scheme.deadline <= next_month,
                Scheme.status == 'OPEN',
            ).order_by(Scheme.deadline).all()

            # Pending proposals
            pending_proposals = Proposal.query.filter(
                Proposal.status.in_(['DRAFT', 'UNDER_REVIEW']),
            ).count()

            subject = f"[Monthly Digest] GTU-ITR R&D Portal — {now.strftime('%B %Y')}"

            body = (
                f"Dear Faculty Member,\n\n"
                f"Here is your monthly R&D digest for {now.strftime('%B %Y')}:\n\n"
            )

            # Upcoming deadlines section
            body += "═══ UPCOMING DEADLINES ═══\n"
            if upcoming_schemes:
                for s in upcoming_schemes:
                    days = s.days_until_deadline
                    body += (
                        f"  • {s.title} — Deadline: "
                        f"{s.deadline.strftime('%d %b %Y')} "
                        f"({days} day{'s' if days != 1 else ''} remaining)\n"
                    )
            else:
                body += "  No upcoming deadlines in the next 30 days.\n"

            # Pending items
            body += f"\n═══ PENDING ITEMS ═══\n"
            body += f"  • {pending_proposals} proposal(s) pending (Draft / Under Review)\n"

            body += (
                f"\n\nPlease log in to the portal to take necessary actions.\n\n"
                f"Best regards,\n"
                f"GTU-ITR R&D & IIC Portal\n"
                f"(This is an automated monthly notification)"
            )

            return cls._send(subject, body, recipients)

        except Exception as exc:
            logger.exception("send_monthly_reminder failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Core send helper
    # ------------------------------------------------------------------

    @classmethod
    def _send(cls, subject: str, body: str, recipients: list[str]) -> bool:
        """
        Build and send a Flask-Mail message.

        Returns True on success, False on failure.
        """
        try:
            if not recipients:
                logger.warning("No recipients specified; skipping email.")
                return False

            sender = current_app.config.get(
                'MAIL_DEFAULT_SENDER', 'noreply@gtu.ac.in'
            )

            msg = Message(
                subject=subject,
                sender=sender,
                recipients=recipients,
                body=body,
            )

            mail.send(msg)
            logger.info(
                "Email sent: '%s' → %s",
                subject,
                ', '.join(recipients[:3]) + ('...' if len(recipients) > 3 else ''),
            )
            return True

        except Exception as exc:
            logger.exception("Failed to send email '%s': %s", subject, exc)
            return False
