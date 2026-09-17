"""
The brief's definition of success, as executable checks.

Section 29 lists eleven things that have to be true when the backend is done.
Asserting them in a hand-off document proves nothing; asserting them here means
they keep being true as the site changes.
"""

import datetime
from decimal import Decimal
from pathlib import Path
from typing import override

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site

from poundit.imports import URL_MAP
from poundit.models import (
    CalendarEntry,
    EventIndexPage,
    EventPage,
    FacultyMember,
    PounditHomePage,
    PounditSettings,
    Program,
    ProgramScheduleEntry,
)

APP_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = APP_ROOT.parent / "templates" / "poundit"


class EditOnceUpdatesEverywhere(TestCase):
    """1. A program is edited once and updates everywhere it appears."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

    def test_a_price_change_reaches_every_page_that_shows_it(self) -> None:
        # A price no other program shares, so the assertions are about this one.
        program = Program.objects.get(slug="lil-cuz")
        program.featured = True
        program.tuition_amount = Decimal("137")
        program.save()

        for path in ("/", "/programs/", "/programs/kids-teen/"):
            with self.subTest(path=path):
                self.assertContains(
                    self.client.get(path, HTTP_HOST="localhost"), "$137 per month"
                )

        program.tuition_amount = Decimal("151")
        program.save()

        for path in ("/", "/programs/", "/programs/kids-teen/"):
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST="localhost")
                self.assertContains(response, "$151 per month")
                self.assertNotContains(response, "$137 per month")

    def test_a_time_change_reaches_the_schedule_and_the_listings(self) -> None:
        entry = ProgramScheduleEntry.objects.filter(program__slug="lil-cuz").first()
        entry.start_time = datetime.time(18, 30)
        entry.end_time = datetime.time(19, 15)
        entry.save()

        for path in ("/schedule/", "/programs/"):
            with self.subTest(path=path):
                self.assertContains(
                    self.client.get(path, HTTP_HOST="localhost"), "6:30-7:15 PM"
                )


class FacultyIsNotDuplicated(TestCase):
    """2. Faculty data is not duplicated."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)

    def test_one_record_per_person(self) -> None:
        slugs = list(FacultyMember.objects.values_list("slug", flat=True))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_an_instructor_teaching_many_sessions_is_still_one_record(self) -> None:
        rico = FacultyMember.objects.get(slug="rico")

        self.assertGreater(rico.schedule_entries.count(), 5)
        self.assertEqual(FacultyMember.objects.filter(name="Rico").count(), 1)

    def test_renaming_a_person_updates_every_session(self) -> None:
        member = FacultyMember.objects.get(slug="dizzylock")
        member.short_name = "Dizzy"
        member.save()

        entry = member.schedule_entries.first()
        self.assertIn("Dizzy", entry.instructor_display)
        self.assertNotIn("Dizzylock", entry.instructor_display)


class ExpiredEventsDisappear(TestCase):
    """3. Future events disappear automatically from upcoming views."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        self.index = EventIndexPage.objects.get(slug="events")

    def _event(self, title: str, days: int, end_days: int | None = None) -> EventPage:
        event = EventPage(
            title=title,
            slug=title.lower().replace(" ", "-"),
            start_datetime=timezone.now() + datetime.timedelta(days=days),
            end_datetime=(
                timezone.now() + datetime.timedelta(days=end_days)
                if end_days is not None
                else None
            ),
        )
        self.index.add_child(instance=event)
        event.save_revision().publish()
        return event

    def test_no_manual_step_is_needed_to_retire_an_event(self) -> None:
        past = self._event("Last Year Battle", -40)
        future = self._event("Next Battle", 40)

        upcoming = list(EventPage.objects.upcoming())

        self.assertIn(future, upcoming)
        self.assertNotIn(past, upcoming)
        self.assertTrue(past.live)  # still published, just no longer upcoming

    def test_a_run_in_progress_is_not_retired_early(self) -> None:
        camp = self._event("Spring Camp", -1, 2)
        self.assertIn(camp, EventPage.objects.upcoming())


class ImportantDatesAreStructured(TestCase):
    """4. Important dates are structured and chronological."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_calendar", verbosity=0)

    def test_dates_are_rows_with_real_date_fields(self) -> None:
        entry = CalendarEntry.objects.get(title="Christmas Break")

        self.assertIsInstance(entry.start_date, datetime.date)
        self.assertIsInstance(entry.end_date, datetime.date)

    def test_default_order_is_chronological(self) -> None:
        dates = list(CalendarEntry.objects.values_list("start_date", flat=True))
        self.assertEqual(dates, sorted(dates))

    def test_the_page_is_generated_not_retyped(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        response = self.client.get("/important-dates/", HTTP_HOST="localhost")

        entries = [
            entry
            for month in response.context["entries_by_month"].values()
            for entry in month
        ]
        self.assertEqual(len(entries), CalendarEntry.objects.count())


class ContactInformationExistsOnce(TestCase):
    """5. Studio contact information exists once."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

    def test_no_page_model_stores_contact_details(self) -> None:
        contact_fields = {"phone_number", "address", "opening_hours", "instagram_url"}

        for model in (PounditHomePage, EventPage):
            with self.subTest(model=model.__name__):
                names = {f.name for f in model._meta.get_fields()}
                self.assertEqual(names & contact_fields, set())

    def test_changing_the_phone_number_once_changes_it_everywhere(self) -> None:
        site = Site.objects.get(is_default_site=True)
        studio_settings = PounditSettings.for_site(site)
        studio_settings.phone_number = "(403) 555-0000"
        studio_settings.save()

        for path in ("/", "/schedule/", "/faculty/"):
            with self.subTest(path=path):
                self.assertContains(
                    self.client.get(path, HTTP_HOST="localhost"), "(403) 555-0000"
                )


class HomePageComposes(TestCase):
    """6. The homepage references other content rather than copying it."""

    def test_it_owns_editorial_copy_and_nothing_factual(self) -> None:
        names = {f.name for f in PounditHomePage._meta.get_fields()}

        for editorial in ("hero_title", "intro_copy", "programs_section_title"):
            self.assertIn(editorial, names)
        for factual in ("tuition_amount", "age_min", "start_time", "phone_number"):
            self.assertNotIn(factual, names)


class WixIsNotARuntimeDependency(TestCase):
    """8. Wix is no longer required as a runtime dependency."""

    def test_no_template_points_at_the_old_host(self) -> None:
        for template in TEMPLATE_ROOT.rglob("*.html"):
            with self.subTest(template=template.name):
                body = template.read_text(encoding="utf-8")
                self.assertNotIn("wixstatic", body)
                self.assertNotIn("pounditdj.com", body)

    def test_no_model_or_block_points_at_the_old_host(self) -> None:
        for source in list((APP_ROOT / "models").glob("*.py")) + [
            APP_ROOT / "blocks.py",
            APP_ROOT / "forms.py",
        ]:
            with self.subTest(source=source.name):
                self.assertNotIn("wixstatic", source.read_text(encoding="utf-8"))

    def test_the_old_host_appears_only_as_provenance(self) -> None:
        """imports.py records where files came from. That is a note, not a fetch."""
        body = (APP_ROOT / "imports.py").read_text(encoding="utf-8")

        self.assertIn("wixstatic", body)
        for fetching in ("requests.get", "urlopen", "urlretrieve", "httpx"):
            self.assertNotIn(fetching, body)


class LegacyUrlsAreHandled(TestCase):
    """9. Legacy URLs are handled intentionally."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        call_command("seed_poundit_redirects", verbosity=0)

    def test_every_known_legacy_path_redirects(self) -> None:
        for legacy in URL_MAP:
            with self.subTest(legacy=legacy):
                response = self.client.get(legacy, HTTP_HOST="localhost")
                self.assertEqual(response.status_code, 301)

    def test_redirects_are_permanent_and_land_on_real_paths(self) -> None:
        for redirect in Redirect.objects.all():
            with self.subTest(path=redirect.old_path):
                self.assertTrue(redirect.is_permanent)
                self.assertTrue(redirect.redirect_link.startswith("/"))


class CodexGetsSemanticData(TestCase):
    """10. Codex receives clean semantic data, not markup built in Python."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)

    def test_no_display_property_emits_html(self) -> None:
        program = Program.objects.get(slug="red-deer-city-breakers")
        entry = program.schedule_entries.first()
        member = FacultyMember.objects.get(slug="rico")

        values = [
            program.age_display,
            program.tuition_display,
            program.schedule_display,
            program.level_colour,
            entry.time_display,
            entry.instructor_display,
            entry.display_label,
            member.display_name,
            member.grid_name,
        ]

        for value in values:
            with self.subTest(value=value):
                self.assertNotIn("<", str(value))
                self.assertNotIn("class=", str(value))

    def test_colour_identifiers_are_tokens_not_values(self) -> None:
        from poundit.models import TrainingLevel

        for level in TrainingLevel.objects.all():
            with self.subTest(level=level.slug):
                self.assertNotIn("#", level.colour_identifier)
                self.assertNotIn("rgb", level.colour_identifier.lower())

    def test_the_schedule_hands_over_a_finished_structure(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        response = self.client.get("/schedule/", HTTP_HOST="localhost")

        day = response.context["schedule"][0]
        self.assertEqual(set(day.keys()), {"weekday", "label", "rooms"})
        self.assertEqual(set(day["rooms"][0].keys()), {"room", "entries"})


class FitsTheExistingArchitecture(TestCase):
    """11. The implementation fits the local system rather than fighting it."""

    # Alternative Naissance still shares this installation. Pound It's explicit
    # parent link keeps both EventPage models accessible without a name clash.

    def test_event_page_owns_an_explicit_parent_link(self) -> None:
        link = EventPage._meta.get_field("page_ptr")

        self.assertTrue(link.remote_field.parent_link)
        self.assertEqual(link.remote_field.related_name, "poundit_eventpage")
        self.assertEqual(EventPage._meta.app_label, "poundit")

    def test_event_page_accessors_resolve_to_their_own_apps(self) -> None:
        from altnaissance.models import EventPage as LegacyEventPage
        from wagtail.models import Page

        self.assertIs(Page._meta.get_field("eventpage").related_model, LegacyEventPage)
        self.assertIs(Page._meta.get_field("poundit_eventpage").related_model, EventPage)

    def test_poundit_has_no_dependency_on_the_split_out_app(self) -> None:
        sources = list((APP_ROOT / "models").glob("*.py")) + [
            APP_ROOT / "blocks.py",
            APP_ROOT / "forms.py",
            APP_ROOT / "imports.py",
        ]
        for source in sources:
            with self.subTest(source=source.name):
                body = source.read_text(encoding="utf-8")
                self.assertNotIn("from altnaissance", body)
                self.assertNotIn("import altnaissance", body)

    def test_it_reuses_the_shared_email_app(self) -> None:
        body = (APP_ROOT / "models" / "inquiries.py").read_text(encoding="utf-8")
        self.assertIn("emails.utils", body)

    def test_alternative_naissance_keeps_its_own_site(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        previous_root = Site.objects.get(is_default_site=True).root_page

        call_command("seed_poundit_site", verbosity=0)

        self.assertTrue(Page.objects.filter(id=previous_root.id).exists())
        self.assertEqual(Site.objects.count(), 2)
