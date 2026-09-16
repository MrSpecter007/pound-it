"""
Tests for the admin experience.

Editors should find one Pound It section rather than six, and should not have
to remember which command printed which warning — anything still needing a
person belongs on the dashboard.
"""

from typing import override

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from poundit.models import FacultyMember, SchoolInquiry
from poundit.wagtail_hooks.viewsets import PounditGroup


class AdminMenuTests(TestCase):
    """One sidebar entry for the studio, not one per model."""

    def test_everything_lives_in_a_single_group(self) -> None:
        self.assertEqual(PounditGroup.menu_label, "Pound It")
        self.assertEqual(len(PounditGroup.items), 12)

    def test_daily_work_comes_before_setup(self) -> None:
        labels = [viewset.menu_label for viewset in PounditGroup.items]

        self.assertEqual(
            labels[:4],
            ["Programs", "Faculty", "Season calendar", "School inquiries"],
        )
        self.assertEqual(labels[-1], "Import ledger")

    def test_no_viewset_registers_its_own_top_level_entry(self) -> None:
        for viewset in PounditGroup.items:
            with self.subTest(viewset=viewset.__name__):
                self.assertFalse(getattr(viewset, "add_to_admin_menu", False))

    def test_submissions_and_ledger_cannot_be_created_by_hand(self) -> None:
        from poundit.wagtail_hooks.viewsets import ImportLedgerViewSet, SchoolInquiryViewSet

        self.assertFalse(SchoolInquiryViewSet.add_view_enabled)
        self.assertFalse(ImportLedgerViewSet.add_view_enabled)
        self.assertFalse(ImportLedgerViewSet.edit_view_enabled)

    def test_inquiries_stay_editable_so_staff_can_mark_them_handled(self) -> None:
        from poundit.wagtail_hooks.viewsets import SchoolInquiryViewSet

        self.assertNotEqual(getattr(SchoolInquiryViewSet, "edit_view_enabled", True), False)


class AdminListingTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)

        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(self.user)

    def test_program_listing_loads(self) -> None:
        response = self.client.get("/admin/snippets/poundit/program/")
        self.assertEqual(response.status_code, 200)

    def test_program_listing_shows_when_each_program_runs(self) -> None:
        response = self.client.get("/admin/snippets/poundit/program/")
        self.assertContains(response, "Mondays 5:15-6:00 PM")

    def test_faculty_listing_loads(self) -> None:
        response = self.client.get("/admin/snippets/poundit/facultymember/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dizzylock")

    def test_program_edit_view_loads(self) -> None:
        from poundit.models import Program

        program = Program.objects.get(slug="red-deer-city-breakers")
        response = self.client.get(f"/admin/snippets/poundit/program/edit/{program.pk}/")

        self.assertEqual(response.status_code, 200)
        # The grouped panels from the brief.
        for heading in ("Eligibility", "Schedule", "Pricing", "Registration", "Publishing"):
            self.assertContains(response, heading)


class DashboardPanelTests(TestCase):
    @override
    def setUp(self) -> None:
        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(self.user)

    def test_panel_is_hidden_when_there_is_nothing_to_do(self) -> None:
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "needs a person")

    def test_panel_appears_once_there_is_something_outstanding(self) -> None:
        SchoolInquiry.objects.create(
            school_name="Riverside Elementary",
            contact_name="Dana Okafor",
            email="dana@riverside.example.com",
        )

        response = self.client.get("/admin/")

        self.assertContains(response, "needs a person")
        self.assertContains(response, "school inquiry awaiting a reply")

    def test_handled_inquiries_drop_off_the_panel(self) -> None:
        inquiry = SchoolInquiry.objects.create(
            school_name="Riverside Elementary",
            contact_name="Dana Okafor",
            email="dana@riverside.example.com",
        )
        inquiry.handled = True
        inquiry.save()

        response = self.client.get("/admin/")
        self.assertNotContains(response, "awaiting a reply")

    def test_panel_counts_the_real_gaps_after_a_full_import(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)
        call_command("seed_poundit_calendar", verbosity=0)

        response = self.client.get("/admin/")

        self.assertContains(response, "weekly sessions with no instructor")
        self.assertContains(response, "faculty without a biography")
        self.assertContains(response, "calendar dates still tentative")

    def test_a_completed_bio_reduces_the_count(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)

        from poundit.wagtail_hooks.panels import PounditReviewPanel

        before = self._count(PounditReviewPanel, "faculty without a biography")

        member = FacultyMember.objects.get(slug="rico")
        member.full_bio = "<p>Pasted verbatim.</p>"
        member.save()

        after = self._count(PounditReviewPanel, "faculty without a biography")

        self.assertEqual(after, before - 1)

    def _count(self, panel_class, label: str) -> int:
        request = self.client.get("/admin/").wsgi_request
        panel = panel_class(request)
        for item in panel.outstanding:
            if item["label"] == label:
                return item["count"]
        return 0


# NoRegressionForTheOtherSiteTests used to live here. It asserted that
# Alternative Naissance's own admin sections -- /admin/inscription/ and
# /admin/candidatures/ -- still answered 200 after Pound It's snippets were
# registered, because both sites shared one Wagtail admin.
#
# Alternative Naissance has been split out of this repository, so there is no
# other site left to regress. The guard that still matters is
# PounditAdminGroupTests below: Pound It's own snippets must stay reachable and
# grouped under one menu item.
