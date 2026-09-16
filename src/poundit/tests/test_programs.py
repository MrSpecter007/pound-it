"""
Tests for programs, the weekly schedule, and the grid the front end renders from.

Covers:
- display properties (age, tuition, times) including the tiered-price case
- the public/featured/category/season querysets
- exclusion of non-offerings such as studio rentals and private training
- grid shape and ordering
- seed command counts and idempotency
"""

import datetime
from decimal import Decimal
from typing import override

from django.core.management import call_command
from django.test import TestCase

from poundit.models import (
    Program,
    ProgramCategory,
    ProgramInclusion,
    ProgramScheduleEntry,
    ProgramTuitionOption,
    Season,
    StudioRoom,
    TrainingLevel,
    Weekday,
)


class ProgramDisplayTests(TestCase):
    """The human-readable properties templates rely on."""

    def test_age_display_from_a_range(self) -> None:
        program = Program.objects.create(title="Chicos", slug="chicos", age_min=6, age_max=9)
        self.assertEqual(program.age_display, "Ages 6-9")

    def test_age_display_from_a_minimum_only(self) -> None:
        program = Program.objects.create(title="AK42s", slug="ak42s", age_min=18)
        self.assertEqual(program.age_display, "Ages 18+")

    def test_age_label_overrides_the_generated_range(self) -> None:
        program = Program.objects.create(
            title="Revolution", slug="revolution", age_min=6, age_max=99, age_label="All ages"
        )
        self.assertEqual(program.age_display, "All ages")

    def test_age_display_is_empty_when_unknown(self) -> None:
        program = Program.objects.create(title="Open House", slug="open-house")
        self.assertEqual(program.age_display, "")

    def test_tuition_display_drops_trailing_zeros(self) -> None:
        program = Program.objects.create(
            title="Chicos", slug="chicos", tuition_amount=Decimal("135.00"), tuition_period="month"
        )
        self.assertEqual(program.tuition_display, "$135 per month")

    def test_tuition_display_keeps_real_cents(self) -> None:
        program = Program.objects.create(
            title="Odd", slug="odd", tuition_amount=Decimal("99.50"), tuition_period="month"
        )
        self.assertEqual(program.tuition_display, "$99.50 per month")

    def test_tiered_tuition_falls_back_to_the_first_option(self) -> None:
        program = Program.objects.create(title="PIBA", slug="piba")
        ProgramTuitionOption.objects.create(
            program=program, label="1 class per week", amount=Decimal("70"),
            period="month", sort_order=1,
        )
        ProgramTuitionOption.objects.create(
            program=program, label="Drop-in", amount=Decimal("25"), period="class", sort_order=2,
        )

        self.assertTrue(program.has_tiered_tuition)
        self.assertEqual(program.tuition_display, "$70 per month")

    def test_tuition_display_is_empty_when_no_price_is_published(self) -> None:
        program = Program.objects.create(title="Open Locking", slug="open-locking")
        self.assertEqual(program.tuition_display, "")

    def test_level_colour_is_the_semantic_token(self) -> None:
        level = TrainingLevel.objects.create(
            name="Crew", slug="crew", display_label="Crew Class", colour_identifier="crew"
        )
        program = Program.objects.create(title="Lil Cuz", slug="lil-cuz", level=level)
        self.assertEqual(program.level_colour, "crew")

    def test_level_colour_is_empty_without_a_level(self) -> None:
        program = Program.objects.create(title="Untyped", slug="untyped")
        self.assertEqual(program.level_colour, "")

    def test_registration_url_falls_back_to_the_studio_default(self) -> None:
        class FakeSettings:
            registration_url = "https://example.com/register"

        program = Program.objects.create(title="Chicos", slug="chicos")
        self.assertEqual(program.get_registration_url(FakeSettings()), "https://example.com/register")

    def test_registration_url_prefers_the_program_override(self) -> None:
        class FakeSettings:
            registration_url = "https://example.com/register"

        program = Program.objects.create(
            title="Chicos", slug="chicos", registration_url="https://example.com/chicos"
        )
        self.assertEqual(program.get_registration_url(FakeSettings()), "https://example.com/chicos")


class ScheduleEntryTests(TestCase):
    """A weekly session stores real times, and formats them only for display."""

    @override
    def setUp(self) -> None:
        self.room = StudioRoom.objects.create(name="Notorious BIG", slug="notorious-big")
        self.program = Program.objects.create(title="Lil Cuz Crew", slug="lil-cuz")

    def _entry(self, start: str, end: str, **kwargs) -> ProgramScheduleEntry:
        h1, m1 = start.split(":")
        h2, m2 = end.split(":")
        return ProgramScheduleEntry.objects.create(
            program=self.program,
            weekday=Weekday.MONDAY,
            start_time=datetime.time(int(h1), int(m1)),
            end_time=datetime.time(int(h2), int(m2)),
            room=self.room,
            **kwargs,
        )

    def test_time_display_collapses_a_shared_meridiem(self) -> None:
        self.assertEqual(self._entry("17:15", "18:00").time_display, "5:15-6:00 PM")

    def test_time_display_keeps_both_when_the_meridiem_changes(self) -> None:
        self.assertEqual(self._entry("11:30", "12:30").time_display, "11:30 AM-12:30 PM")

    def test_duration_in_minutes(self) -> None:
        self.assertEqual(self._entry("17:15", "18:00").duration_minutes, 45)

    def test_label_defaults_to_the_program_title(self) -> None:
        self.assertEqual(self._entry("17:15", "18:00").display_label, "Lil Cuz Crew")

    def test_label_overrides_the_program_title(self) -> None:
        entry = self._entry("19:00", "20:00", label="Power & Strength Training")
        self.assertEqual(entry.display_label, "Power & Strength Training")

    def test_a_program_can_hold_several_weekly_sessions(self) -> None:
        self._entry("17:15", "18:00")
        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.WEDNESDAY,
            start_time=datetime.time(17, 15), end_time=datetime.time(18, 0), room=self.room,
        )
        self.assertEqual(self.program.schedule_entries.count(), 2)

    def test_schedule_display_summarises_every_session(self) -> None:
        self._entry("17:15", "18:00")
        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.WEDNESDAY,
            start_time=datetime.time(18, 0), end_time=datetime.time(18, 45), room=self.room,
        )
        self.assertEqual(
            self.program.schedule_display,
            "Mondays 5:15-6:00 PM, Wednesdays 6:00-6:45 PM",
        )


class ProgramQuerySetTests(TestCase):
    """Listings must never show schedule occupancy as though it were enrollable."""

    @override
    def setUp(self) -> None:
        self.kids = ProgramCategory.objects.create(name="Kids & Teen Rec", slug="kids-teen")
        self.other = ProgramCategory.objects.create(name="Other", slug="other")

        self.public_program = Program.objects.create(
            title="Chicos", slug="chicos", category=self.kids, featured=True
        )
        self.rentals = Program.objects.create(
            title="Studio Rentals", slug="studio-rentals", category=self.other, is_public=False
        )
        self.retired = Program.objects.create(
            title="Retired Crew", slug="retired", category=self.kids, active=False
        )

    def test_public_excludes_non_offerings(self) -> None:
        self.assertNotIn(self.rentals, Program.objects.public())

    def test_public_excludes_inactive_programs(self) -> None:
        self.assertNotIn(self.retired, Program.objects.public())

    def test_featured_is_a_subset_of_public(self) -> None:
        self.assertEqual(list(Program.objects.featured()), [self.public_program])

    def test_for_category_accepts_a_slug_or_an_instance(self) -> None:
        self.assertEqual(list(Program.objects.for_category("kids-teen")), [self.public_program])
        self.assertEqual(list(Program.objects.for_category(self.kids)), [self.public_program])

    def test_for_season_returns_nothing_when_no_season_is_set(self) -> None:
        self.assertEqual(list(Program.objects.for_season(None)), [])


class ScheduleGridTests(TestCase):
    """The grid is shaped in Python so templates never filter."""

    @override
    def setUp(self) -> None:
        self.season = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)
        self.nb = StudioRoom.objects.create(name="Notorious BIG", slug="notorious-big", sort_order=10)
        self.by = StudioRoom.objects.create(name="Black & Yellow", slug="black-and-yellow", sort_order=20)
        self.program = Program.objects.create(title="Lil Cuz", slug="lil-cuz")
        self.hidden = Program.objects.create(title="Rentals", slug="rentals", is_public=False)

        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.MONDAY, season=self.season,
            start_time=datetime.time(18, 0), end_time=datetime.time(18, 45), room=self.nb,
        )
        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.MONDAY, season=self.season,
            start_time=datetime.time(17, 15), end_time=datetime.time(18, 0), room=self.nb,
        )
        ProgramScheduleEntry.objects.create(
            program=self.program, weekday=Weekday.TUESDAY, season=self.season,
            start_time=datetime.time(17, 15), end_time=datetime.time(18, 0), room=self.by,
        )
        ProgramScheduleEntry.objects.create(
            program=self.hidden, weekday=Weekday.MONDAY, season=self.season,
            start_time=datetime.time(16, 30), end_time=datetime.time(17, 15), room=self.nb,
        )

    def test_grid_is_keyed_by_weekday_then_room(self) -> None:
        grid = ProgramScheduleEntry.objects.for_season(self.season).grid()

        self.assertEqual(sorted(grid.keys()), [Weekday.MONDAY, Weekday.TUESDAY])
        self.assertIn(self.nb.id, grid[Weekday.MONDAY])
        self.assertIn(self.by.id, grid[Weekday.TUESDAY])

    def test_entries_within_a_room_are_ordered_by_start_time(self) -> None:
        grid = ProgramScheduleEntry.objects.for_season(self.season).public().grid()
        monday = grid[Weekday.MONDAY][self.nb.id]

        self.assertEqual(
            [entry.time_display for entry in monday],
            ["5:15-6:00 PM", "6:00-6:45 PM"],
        )

    def test_public_grid_omits_non_offerings(self) -> None:
        grid = ProgramScheduleEntry.objects.for_season(self.season).public().grid()
        labels = [entry.display_label for entry in grid[Weekday.MONDAY][self.nb.id]]
        self.assertNotIn("Rentals", labels)

    def test_for_season_with_no_season_is_empty(self) -> None:
        self.assertEqual(ProgramScheduleEntry.objects.for_season(None).grid(), {})


class ScheduleSeedCommandTests(TestCase):
    """The seed reproduces the printed schedule and survives being re-run."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)

    def test_seeds_every_program_and_session(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)

        self.assertEqual(Program.objects.count(), 34)
        self.assertEqual(ProgramScheduleEntry.objects.count(), 44)

    def test_non_offerings_are_flagged_not_public(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)

        self.assertFalse(Program.objects.get(slug="studio-rentals").is_public)
        self.assertFalse(Program.objects.get(slug="private-training").is_public)
        self.assertEqual(Program.objects.public().count(), 32)

    def test_rerunning_creates_no_duplicates(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)

        self.assertEqual(Program.objects.count(), 34)
        self.assertEqual(ProgramScheduleEntry.objects.count(), 44)

    def test_dry_run_writes_nothing(self) -> None:
        call_command("seed_poundit_schedule", "--dry-run", verbosity=0)
        self.assertEqual(Program.objects.count(), 0)

    def test_breakers_gets_two_differently_labelled_sessions(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)
        breakers = Program.objects.get(slug="red-deer-city-breakers")

        labels = sorted(entry.display_label for entry in breakers.schedule_entries.all())
        self.assertEqual(labels, ["Crew Choreography", "Power & Strength Training"])
        self.assertTrue(breakers.audition_required)

    def test_piba_keeps_all_five_tuition_tiers(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)
        piba = Program.objects.get(slug="piba")

        self.assertEqual(piba.tuition_options.count(), 5)
        self.assertIsNone(piba.tuition_amount)
        self.assertEqual(piba.tuition_display, "$70 per month")

    def test_inclusions_are_rows_not_prose(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)
        lil_cuz = Program.objects.get(slug="lil-cuz")

        self.assertEqual(
            [i.text for i in lil_cuz.inclusions.all()],
            ["2 performances", "Costume"],
        )

    def test_every_entry_is_attached_to_the_current_season(self) -> None:
        call_command("seed_poundit_schedule", verbosity=0)
        season = Season.current()

        self.assertEqual(
            ProgramScheduleEntry.objects.exclude(season=season).count(), 0
        )

    def test_command_refuses_without_a_season(self) -> None:
        Season.objects.all().delete()
        call_command("seed_poundit_schedule", verbosity=0)
        self.assertEqual(Program.objects.count(), 0)
