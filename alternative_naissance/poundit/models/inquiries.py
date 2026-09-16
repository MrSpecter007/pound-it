"""
School residency inquiries.

The source site puts the same contact form on the page twice. This is the one
intentional flow: a single model, a single form, posting back to the page it
lives on. Notifications go through the project's existing ``emails`` app so the
wording stays editable in the admin rather than being baked into code.
"""

import logging

from django.conf import settings as django_settings
from django.db import models

logger = logging.getLogger(__name__)

INQUIRY_CONFIRMATION = "poundit_school_inquiry_confirmation"
INQUIRY_ADMIN_NOTIFICATION = "poundit_school_inquiry_admin_notification"


class SchoolInquiry(models.Model):
    """A school asking about booking a residency."""

    school_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    preferred_dates = models.CharField(
        max_length=255,
        blank=True,
        help_text="Free text, as the school wrote it.",
    )
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(
        default=False,
        help_text="Tick once someone has replied to this school.",
    )
    staff_notes = models.TextField(
        blank=True,
        help_text="Internal only. Never shown to the school.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "School inquiry"
        verbose_name_plural = "School inquiries"

    def __str__(self) -> str:
        return f"{self.school_name} - {self.contact_name}"

    @property
    def email_context(self) -> dict:
        return {
            "school_name": self.school_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "preferred_dates": self.preferred_dates,
            "message": self.message,
            "submitted_date": self.created_at.strftime("%-d %B %Y") if self.created_at else "",
        }


def send_inquiry_notifications(inquiry: SchoolInquiry, studio_settings=None) -> None:
    """
    Confirm to the school, and tell the studio.

    Best effort: a mail failure must never lose the inquiry, which is already
    saved by the time this runs.
    """
    from emails.utils import send_templated_email

    context = inquiry.email_context

    try:
        send_templated_email(
            scenario=INQUIRY_CONFIRMATION,
            context=context,
            to_emails=[inquiry.email],
        )
    except Exception:
        logger.exception("School inquiry confirmation failed for %s", inquiry.pk)

    recipient = getattr(studio_settings, "public_email", "") or getattr(
        django_settings, "ADMIN_EMAIL", ""
    )
    if not recipient:
        logger.warning(
            "School inquiry %s saved but no studio recipient is configured. "
            "Set Public email in Pound It settings or ADMIN_EMAIL.",
            inquiry.pk,
        )
        return

    try:
        send_templated_email(
            scenario=INQUIRY_ADMIN_NOTIFICATION,
            context=context,
            to_emails=[recipient],
        )
    except Exception:
        logger.exception("School inquiry notification failed for %s", inquiry.pk)
