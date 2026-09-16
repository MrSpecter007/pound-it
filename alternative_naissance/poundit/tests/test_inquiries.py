"""
Tests for the school residency page and its inquiry flow.

The source site renders the same contact form twice on one page. The point of
these tests is that there is exactly one form, it posts back to its own page,
a refresh cannot resubmit it, and a mail failure never loses the inquiry.
"""

from typing import override
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Site

from emails.models import EmailTemplate
from poundit.forms import SchoolInquiryForm
from poundit.models import (
    PounditHomePage,
    PounditSettings,
    SchoolInquiry,
    SchoolProgramsPage,
)


class SchoolInquiryFormTests(TestCase):
    def _payload(self, **overrides) -> dict:
        data = {
            "school_name": "Riverside Elementary",
            "contact_name": "Dana Okafor",
            "email": "dana@riverside.example.com",
            "phone": "403-555-0123",
            "preferred_dates": "Any week in March",
            "message": "Grades 4 to 6, about 60 students.",
        }
        data.update(overrides)
        return data

    def test_valid_submission(self) -> None:
        self.assertTrue(SchoolInquiryForm(self._payload()).is_valid())

    def test_school_contact_and_email_are_required(self) -> None:
        for field in ("school_name", "contact_name", "email"):
            with self.subTest(field=field):
                form = SchoolInquiryForm(self._payload(**{field: ""}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_phone_and_dates_are_optional(self) -> None:
        form = SchoolInquiryForm(self._payload(phone="", preferred_dates=""))
        self.assertTrue(form.is_valid())

    def test_malformed_email_is_rejected(self) -> None:
        form = SchoolInquiryForm(self._payload(email="not-an-address"))
        self.assertFalse(form.is_valid())

    def test_honeypot_rejects_automated_submissions(self) -> None:
        form = SchoolInquiryForm(self._payload(website="http://spam.example.com"))
        self.assertFalse(form.is_valid())

    def test_internal_admin_help_text_never_reaches_the_public_form(self) -> None:
        for field in SchoolInquiryForm().fields.values():
            self.assertEqual(field.help_text, "")


class SchoolProgramsPageTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        self.page = SchoolProgramsPage.objects.get(slug="school-programs")
        self.path = "/school-programs/"

    def _post(self, **overrides):
        data = {
            "school_name": "Riverside Elementary",
            "contact_name": "Dana Okafor",
            "email": "dana@riverside.example.com",
            "phone": "403-555-0123",
            "preferred_dates": "Any week in March",
            "message": "",
            "website": "",
        }
        data.update(overrides)
        return self.client.post(self.path, data, HTTP_HOST="localhost")

    def test_page_renders_with_one_form(self) -> None:
        response = self.client.get(self.path, HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().count("<form"), 1)

    def test_seeded_facts_are_present(self) -> None:
        self.assertEqual(self.page.grade_range, "Kindergarten to Grade 9")
        self.assertIn("Four days", self.page.duration_label)

    def test_descriptive_copy_is_left_for_a_human(self) -> None:
        self.assertEqual(self.page.introduction, "")

    def test_valid_submission_is_saved(self) -> None:
        self._post()

        inquiry = SchoolInquiry.objects.get()
        self.assertEqual(inquiry.school_name, "Riverside Elementary")
        self.assertEqual(inquiry.contact_name, "Dana Okafor")
        self.assertFalse(inquiry.handled)

    def test_submission_redirects_so_a_refresh_cannot_resend(self) -> None:
        response = self._post()

        self.assertEqual(response.status_code, 302)
        self.assertIn("submitted=1", response["Location"])

    def test_success_message_shows_after_the_redirect(self) -> None:
        response = self.client.get(f"{self.path}?submitted=1", HTTP_HOST="localhost")

        self.assertTrue(response.context["submitted"])
        self.assertContains(response, self.page.inquiry_success_message)

    def test_success_view_hides_the_form(self) -> None:
        response = self.client.get(f"{self.path}?submitted=1", HTTP_HOST="localhost")
        self.assertEqual(response.content.decode().count("<form"), 0)

    def test_invalid_submission_redisplays_with_errors_and_saves_nothing(self) -> None:
        response = self._post(email="")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SchoolInquiry.objects.exists())
        self.assertTrue(response.context["form"].errors)

    def test_honeypot_submission_is_not_saved(self) -> None:
        self._post(website="http://spam.example.com")
        self.assertFalse(SchoolInquiry.objects.exists())

    def test_form_can_be_turned_off(self) -> None:
        self.page.show_inquiry_form = False
        self.page.save_revision().publish()

        response = self.client.get(self.path, HTTP_HOST="localhost")
        self.assertEqual(response.content.decode().count("<form"), 0)


class InquiryNotificationTests(TestCase):
    """Notifications go through the project's editable email templates."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        self.page = SchoolProgramsPage.objects.get(slug="school-programs")

        site = Site.objects.get(is_default_site=True)
        self.settings_obj = PounditSettings.for_site(site)
        self.settings_obj.public_email = "studio@poundit.example.com"
        self.settings_obj.save()

    def _post(self):
        return self.client.post(
            "/school-programs/",
            {
                "school_name": "Riverside Elementary",
                "contact_name": "Dana Okafor",
                "email": "dana@riverside.example.com",
                "phone": "403-555-0123",
                "preferred_dates": "Any week in March",
                "message": "",
                "website": "",
            },
            HTTP_HOST="localhost",
        )

    def test_email_templates_are_registered_by_the_app(self) -> None:
        for scenario in (
            "poundit_school_inquiry_confirmation",
            "poundit_school_inquiry_admin_notification",
        ):
            self.assertTrue(EmailTemplate.objects.filter(scenario=scenario).exists(), scenario)

    def test_both_notifications_are_sent(self) -> None:
        self._post()

        self.assertEqual(len(mail.outbox), 2)
        recipients = sorted(address for message in mail.outbox for address in message.to)
        self.assertEqual(
            recipients, ["dana@riverside.example.com", "studio@poundit.example.com"]
        )

    def test_notification_carries_the_inquiry_details(self) -> None:
        self._post()

        admin_message = next(m for m in mail.outbox if "studio@poundit.example.com" in m.to)
        self.assertIn("Riverside Elementary", admin_message.subject)
        self.assertIn("Any week in March", admin_message.body)

    def test_studio_email_falls_back_to_the_admin_setting(self) -> None:
        self.settings_obj.public_email = ""
        self.settings_obj.save()

        with self.settings(ADMIN_EMAIL="fallback@example.com"):
            self._post()

        recipients = [address for message in mail.outbox for address in message.to]
        self.assertIn("fallback@example.com", recipients)

    def test_a_mail_failure_never_loses_the_inquiry(self) -> None:
        with patch(
            "emails.utils.send_templated_email", side_effect=RuntimeError("SMTP down")
        ):
            response = self._post()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SchoolInquiry.objects.count(), 1)

    def test_missing_recipient_is_logged_not_raised(self) -> None:
        self.settings_obj.public_email = ""
        self.settings_obj.save()

        with self.settings(ADMIN_EMAIL=""):
            response = self._post()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SchoolInquiry.objects.count(), 1)
        # The school still gets its confirmation even with no studio address set.
        self.assertEqual(len(mail.outbox), 1)
