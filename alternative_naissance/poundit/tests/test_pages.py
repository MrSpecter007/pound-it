"""
Tests for the public page tree.

The point of these is that the home page composes rather than copies: it owns
headings and CTA labels, and every fact on it is read live from a program,
faculty member or event. Index pages hand templates finished lists so no
filtering happens in markup.
"""

import datetime
from decimal import Decimal
from typing import override

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page, Site

from poundit.models import (
    CalendarCategory,
    CalendarEntry,
    ContentPage,
    EventIndexPage,
    EventPage,
    FacultyIndexPage,
    FacultyMember,
    ImportantDatesPage,
    PounditHomePage,
    PounditSettings,
    Program,
    ProgramCategory,
    ProgramIndexPage,
    ProgramScheduleEntry,
    SchedulePage,
    Season,
    StudioRoom,
    TrainingLevel,
    Weekday,
)


class PageTreeRulesTests(TestCase):
    """Editors should not be able to build a nonsensical tree."""

    @override
    def setUp(self) -> None:
        self.root = Page.objects.filter(depth=1).first()
        self.home = PounditHomePage(title="Pound It", slug="poundit")
        self.root.add_child(instance=self.home)

    def test_home_page_accepts_every_section(self) -> None:
        allowed = PounditHomePage.subpage_types
        for model in (
            "poundit.ProgramIndexPage",
            "poundit.SchedulePage",
            "poundit.FacultyIndexPage",
            "poundit.EventIndexPage",
            "poundit.ImportantDatesPage",
            "poundit.ContentPage",
        ):
            self.assertIn(model, allowed)

    def test_sections_may_only_live_under_the_home_page(self) -> None:
        for model in (ProgramIndexPage, SchedulePage, FacultyIndexPage, ImportantDatesPage):
            self.assertEqual(model.parent_page_types, ["poundit.PounditHomePage"])

    def test_events_live_under_the_events_index(self) -> None:
        self.assertEqual(EventPage.parent_page_types, ["poundit.EventIndexPage"])
        self.assertEqual(EventIndexPage.subpage_types, ["poundit.EventPage"])

    def test_content_pages_may_nest(self) -> None:
        self.assertIn("poundit.ContentPage", ContentPage.subpage_types)


class HomePageCompositionTests(TestCase):
    """The home page references other content; it never stores a copy of it."""

    @override
    def setUp(self) -> None:
        site_root = Site.objects.get(is_default_site=True).root_page
        self.home = PounditHomePage(
            title="Pound It", slug="poundit", hero_title="Central Alberta's home of hip hop"
        )
        site_root.add_child(instance=self.home)
        self.home.save_revision().publish()

        self.level = TrainingLevel.objects.create(
            name="Crew", slug="crew", display_label="Crew Class", colour_identifier="crew"
        )
        self.featured = Program.objects.create(
            title="Lil Cuz", slug="lil-cuz", featured=True, level=self.level,
            tuition_amount=Decimal("135"), tuition_period="month",
        )
        Program.objects.create(title="Quiet", slug="quiet", featured=False)
        Program.objects.create(title="Rentals", slug="rentals", featured=True, is_public=False)

        self.member = FacultyMember.objects.create(name="Rico", slug="rico", featured=True)

    def test_context_exposes_the_composed_sections(self) -> None:
        response = self.client.get(self.home.url)

        self.assertEqual(response.status_code, 200)
        for key in (
            "featured_programs",
            "featured_faculty",
            "upcoming_events",
            "training_levels",
            "season",
        ):
            self.assertIn(key, response.context)

    def test_featured_programs_exclude_non_offerings(self) -> None:
        response = self.client.get(self.home.url)
        titles = [p.title for p in response.context["featured_programs"]]

        self.assertIn("Lil Cuz", titles)
        self.assertNotIn("Rentals", titles)
        self.assertNotIn("Quiet", titles)

    def test_home_page_stores_no_program_facts_of_its_own(self) -> None:
        """Editing a program must be enough; the home page has nowhere to disagree."""
        field_names = {f.name for f in PounditHomePage._meta.get_fields()}

        for leaked in ("tuition_amount", "age_min", "start_time", "registration_url"):
            self.assertNotIn(leaked, field_names)

    def test_price_shown_on_the_home_page_follows_the_program(self) -> None:
        response = self.client.get(self.home.url)
        self.assertContains(response, "$135 per month")

        self.featured.tuition_amount = Decimal("145")
        self.featured.save()

        response = self.client.get(self.home.url)
        self.assertContains(response, "$145 per month")
        self.assertNotContains(response, "$135 per month")

    def test_legend_only_carries_public_levels(self) -> None:
        TrainingLevel.objects.create(
            name="Private", slug="private", display_label="Private",
            colour_identifier="private", show_in_legend=False,
        )
        response = self.client.get(self.home.url)

        slugs = [level.slug for level in response.context["training_levels"]]
        self.assertIn("crew", slugs)
        self.assertNotIn("private", slugs)

    def test_featured_overrides_the_fallback(self) -> None:
        response = self.client.get(self.home.url)
        titles = [p.title for p in response.context["featured_programs"]]
        self.assertEqual(titles, ["Lil Cuz"])

    def test_programs_fall_back_to_public_when_nothing_is_featured(self) -> None:
        """A fresh install should never show an empty home page."""
        Program.objects.update(featured=False)

        response = self.client.get(self.home.url)
        titles = [p.title for p in response.context["featured_programs"]]

        self.assertIn("Lil Cuz", titles)
        self.assertIn("Quiet", titles)
        self.assertNotIn("Rentals", titles)

    def test_faculty_fall_back_to_the_regular_roster(self) -> None:
        FacultyMember.objects.update(featured=False)
        FacultyMember.objects.create(name="Genie", slug="genie", is_occasional=True)

        response = self.client.get(self.home.url)
        names = [m.name for m in response.context["featured_faculty"]]

        self.assertIn("Rico", names)
        self.assertNotIn("Genie", names)


class SettingsRenderTests(TestCase):
    """
    The project has no settings context processor, so templates read settings
    through the tag. Without it the header and footer render blank.
    """

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        self.home = PounditHomePage.objects.get(slug="poundit")

    def test_studio_details_reach_the_page(self) -> None:
        response = self.client.get("/", HTTP_HOST="localhost")

        self.assertContains(response, "Pound It Hip Hop Studios")
        self.assertContains(response, "(403) 896-7935")
        self.assertContains(response, "Red Deer, AB T4N 4H8")

    def test_social_links_render_from_settings(self) -> None:
        response = self.client.get("/", HTTP_HOST="localhost")

        self.assertContains(response, "instagram.com/poundithiphopstudios")
        self.assertContains(response, "tiktok.com/@poundithiphopstudio")

    def test_registration_cta_falls_back_to_the_studio_url(self) -> None:
        self.home.primary_cta_label = "Register"
        self.home.primary_cta_url = ""
        self.home.save_revision().publish()

        response = self.client.get("/", HTTP_HOST="localhost")
        self.assertContains(response, "app.gostudiopro.com/online/pounditreddeer")


class SchedulePageTests(TestCase):
    @override
    def setUp(self) -> None:
        site_root = Site.objects.get(is_default_site=True).root_page
        self.home = PounditHomePage(title="Pound It", slug="poundit")
        site_root.add_child(instance=self.home)
        self.page = SchedulePage(title="Schedule", slug="schedule")
        self.home.add_child(instance=self.page)
        self.page.save_revision().publish()

        self.season = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)
        self.nb = StudioRoom.objects.create(name="Notorious BIG", slug="notorious-big", sort_order=10)
        self.by = StudioRoom.objects.create(name="Black & Yellow", slug="black-and-yellow", sort_order=20)
        self.program = Program.objects.create(title="Lil Cuz", slug="lil-cuz")

        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.MONDAY, season=self.season,
            start_time=datetime.time(17, 15), end_time=datetime.time(18, 0), room=self.nb,
        )

    def test_schedule_is_a_finished_nested_list(self) -> None:
        response = self.client.get(self.page.url)
        schedule = response.context["schedule"]

        self.assertEqual(len(schedule), 1)
        day = schedule[0]
        self.assertEqual(day["weekday"], Weekday.MONDAY)
        self.assertEqual(day["label"], "Monday")
        self.assertEqual([c["room"].slug for c in day["rooms"]], ["notorious-big", "black-and-yellow"])

    def test_rooms_without_sessions_render_as_empty_columns(self) -> None:
        response = self.client.get(self.page.url)
        columns = response.context["schedule"][0]["rooms"]

        self.assertEqual(len(columns[0]["entries"]), 1)
        self.assertEqual(columns[1]["entries"], [])

    def test_grid_is_still_available_for_python(self) -> None:
        response = self.client.get(self.page.url)
        self.assertIn(Weekday.MONDAY, response.context["grid"])

    def test_session_details_render(self) -> None:
        response = self.client.get(self.page.url)
        self.assertContains(response, "5:15-6:00 PM")
        self.assertContains(response, "Lil Cuz")


class ProgramIndexPageTests(TestCase):
    @override
    def setUp(self) -> None:
        site_root = Site.objects.get(is_default_site=True).root_page
        self.home = PounditHomePage(title="Pound It", slug="poundit")
        site_root.add_child(instance=self.home)
        self.page = ProgramIndexPage(title="Programs", slug="programs")
        self.home.add_child(instance=self.page)
        self.page.save_revision().publish()

        self.kids = ProgramCategory.objects.create(name="Kids & Teen Rec", slug="kids-teen", sort_order=10)
        self.adult = ProgramCategory.objects.create(name="Adult Rec", slug="adult", sort_order=20)
        Program.objects.create(title="Chicos", slug="chicos", category=self.kids)
        Program.objects.create(title="PIBA", slug="piba", category=self.adult)

    def test_programs_are_grouped_by_category(self) -> None:
        response = self.client.get(self.page.url)
        grouped = dict(
            (category.slug, [p.title for p in programs])
            for category, programs in response.context["programs_by_category"]
        )

        self.assertEqual(grouped["kids-teen"], ["Chicos"])
        self.assertEqual(grouped["adult"], ["PIBA"])

    def test_category_filter_narrows_the_listing(self) -> None:
        response = self.client.get(f"{self.page.url}?category=adult")

        self.assertEqual(response.context["active_category"], "adult")
        slugs = [c.slug for c, _ in response.context["programs_by_category"]]
        self.assertEqual(slugs, ["adult"])

    def test_all_categories_stay_available_for_the_filter_nav(self) -> None:
        response = self.client.get(f"{self.page.url}?category=adult")
        self.assertEqual(response.context["all_categories"].count(), 2)


class FacultyIndexPageTests(TestCase):
    @override
    def setUp(self) -> None:
        site_root = Site.objects.get(is_default_site=True).root_page
        self.home = PounditHomePage(title="Pound It", slug="poundit")
        site_root.add_child(instance=self.home)
        self.page = FacultyIndexPage(title="Faculty", slug="faculty")
        self.home.add_child(instance=self.page)
        self.page.save_revision().publish()

        FacultyMember.objects.create(name="Rico", slug="rico", sort_order=10)
        FacultyMember.objects.create(
            name="Genie", slug="genie", is_occasional=True,
            availability_note="Roughly 1-2 sessions per month.", sort_order=90,
        )

    def test_occasional_instructors_are_listed_separately(self) -> None:
        response = self.client.get(self.page.url)

        self.assertEqual([m.name for m in response.context["faculty"]], ["Rico"])
        self.assertEqual([m.name for m in response.context["occasional_faculty"]], ["Genie"])

    def test_availability_note_is_shown_for_occasional_instructors(self) -> None:
        response = self.client.get(self.page.url)
        self.assertContains(response, "Roughly 1-2 sessions per month.")


class ImportantDatesPageTests(TestCase):
    @override
    def setUp(self) -> None:
        site_root = Site.objects.get(is_default_site=True).root_page
        self.home = PounditHomePage(title="Pound It", slug="poundit")
        site_root.add_child(instance=self.home)
        self.page = ImportantDatesPage(title="Important Dates", slug="important-dates")
        self.home.add_child(instance=self.page)
        self.page.save_revision().publish()

        self.season = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)
        self.closure = CalendarCategory.objects.create(name="Closure", slug="closure")
        today = timezone.localdate()

        self.past = CalendarEntry.objects.create(
            title="Long gone", start_date=today - datetime.timedelta(days=60),
            season=self.season, category=self.closure, is_tentative=True,
        )
        self.future = CalendarEntry.objects.create(
            title="Still to come", start_date=today + datetime.timedelta(days=60),
            season=self.season, category=self.closure, is_tentative=True,
        )

    def test_entries_are_grouped_by_month(self) -> None:
        response = self.client.get(self.page.url)
        grouped = response.context["entries_by_month"]

        titles = [e.title for entries in grouped.values() for e in entries]
        self.assertEqual(sorted(titles), ["Long gone", "Still to come"])

    def test_tentative_notice_appears_when_any_entry_is_tentative(self) -> None:
        response = self.client.get(self.page.url)

        self.assertTrue(response.context["has_tentative"])
        self.assertContains(response, "tentative")

    def test_past_dates_can_be_hidden(self) -> None:
        self.page.show_past_dates = False
        self.page.save_revision().publish()

        response = self.client.get(self.page.url)
        titles = [
            e.title for entries in response.context["entries_by_month"].values() for e in entries
        ]

        self.assertEqual(titles, ["Still to come"])

    def test_category_filter_applies(self) -> None:
        response = self.client.get(f"{self.page.url}?category=closure")
        self.assertEqual(response.context["active_category"], "closure")


class SiteSeedCommandTests(TestCase):
    """Building the tree and taking over as the default site."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)

    def test_builds_the_whole_tree(self) -> None:
        call_command("seed_poundit_site", verbosity=0)

        self.assertTrue(PounditHomePage.objects.filter(slug="poundit").exists())
        for model, slug in (
            (ProgramIndexPage, "programs"),
            (SchedulePage, "schedule"),
            (FacultyIndexPage, "faculty"),
            (EventIndexPage, "events"),
            (ImportantDatesPage, "important-dates"),
        ):
            self.assertTrue(model.objects.filter(slug=slug).exists(), slug)

    def test_creates_the_legal_section_with_children(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        legal = ContentPage.objects.get(slug="legal")

        self.assertEqual(
            sorted(c.slug for c in legal.get_children()),
            ["privacy", "refund-policy", "terms", "waiver"],
        )

    def test_pound_it_becomes_the_default_site(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        default = Site.objects.get(is_default_site=True)

        self.assertEqual(default.root_page.slug, "poundit")
        self.assertEqual(Site.objects.filter(is_default_site=True).count(), 1)

    def test_the_previous_site_is_kept_on_its_own_hostname(self) -> None:
        previous = Site.objects.get(is_default_site=True)
        previous_root = previous.root_page

        call_command("seed_poundit_site", verbosity=0)

        previous.refresh_from_db()
        self.assertFalse(previous.is_default_site)
        self.assertEqual(previous.hostname, "alternative-naissance.localhost")
        self.assertTrue(Page.objects.filter(id=previous_root.id).exists())

    def test_no_default_site_flag_leaves_the_existing_site_alone(self) -> None:
        previous = Site.objects.get(is_default_site=True)

        call_command("seed_poundit_site", "--no-default-site", verbosity=0)

        previous.refresh_from_db()
        self.assertTrue(previous.is_default_site)

    def test_settings_are_populated_from_the_source_site(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        site = Site.objects.get(is_default_site=True)
        settings_obj = PounditSettings.for_site(site)

        self.assertEqual(settings_obj.phone_number, "(403) 896-7935")
        self.assertIn("Red Deer", settings_obj.address)
        self.assertIn("gostudiopro", settings_obj.registration_url)
        self.assertEqual(settings_obj.current_season, Season.current())

    def test_settings_do_not_overwrite_admin_edits(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        site = Site.objects.get(is_default_site=True)
        settings_obj = PounditSettings.for_site(site)
        settings_obj.phone_number = "(403) 000-0000"
        settings_obj.save()

        call_command("seed_poundit_site", verbosity=0)

        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.phone_number, "(403) 000-0000")

    def test_rerunning_creates_no_duplicate_pages(self) -> None:
        call_command("seed_poundit_site", verbosity=0)
        before = Page.objects.count()

        call_command("seed_poundit_site", verbosity=0)

        self.assertEqual(Page.objects.count(), before)

    def test_dry_run_writes_nothing(self) -> None:
        call_command("seed_poundit_site", "--dry-run", verbosity=0)
        self.assertFalse(PounditHomePage.objects.exists())


class FullStackRenderTests(TestCase):
    """Every seeded page renders with the real seeded data behind it."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)
        call_command("seed_poundit_calendar", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

    def test_every_page_returns_200(self) -> None:
        for page in Page.objects.live().specific():
            if not page.url:
                continue
            with self.subTest(page=page.slug):
                self.assertEqual(self.client.get(page.url).status_code, 200)

    def test_schedule_renders_the_real_week(self) -> None:
        page = SchedulePage.objects.get(slug="schedule")
        response = self.client.get(page.url)

        self.assertEqual(len(response.context["schedule"]), 5)
        self.assertContains(response, "Notorious BIG")
        self.assertContains(response, "Black &amp; Yellow")
        self.assertContains(response, "Rico / Dizzylock / Breton / Genie")

    def test_schedule_omits_rentals_and_private_training(self) -> None:
        page = SchedulePage.objects.get(slug="schedule")
        response = self.client.get(page.url)

        self.assertNotContains(response, "Studio Rentals")
        self.assertNotContains(response, "Private Training")

    def test_programs_page_shows_real_tuition(self) -> None:
        page = ProgramIndexPage.objects.get(slug="programs")
        response = self.client.get(page.url)

        self.assertContains(response, "$280 per month")
        self.assertContains(response, "Unlimited training pass")

    def test_important_dates_shows_the_season_verbatim(self) -> None:
        page = ImportantDatesPage.objects.get(slug="important-dates")
        response = self.client.get(page.url)

        self.assertContains(response, "One For Then City Edmonton")
        self.assertContains(response, "Tentative")
