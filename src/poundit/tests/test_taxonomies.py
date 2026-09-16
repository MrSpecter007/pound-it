"""
Tests for the Pound It taxonomies and site settings.

Covers:
- deterministic ordering of every vocabulary
- exactly-one-current-season invariant
- the schedule legend filter
- seed command idempotency and its --update / --dry-run modes
- per-site settings isolation from core.SiteSettings
"""

import datetime
from typing import override

from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Site

from poundit.models import (
    CalendarCategory,
    DanceStyle,
    EventType,
    ProgramCategory,
    PounditSettings,
    Season,
    StudioRoom,
    TrainingLevel,
)


class TaxonomyOrderingTests(TestCase):
    """Every vocabulary orders by sort_order then name, so templates never sort."""

    @override
    def setUp(self) -> None:
        DanceStyle.objects.create(name="Zeta", slug="zeta", sort_order=1)
        DanceStyle.objects.create(name="Alpha", slug="alpha", sort_order=2)
        DanceStyle.objects.create(name="Beta", slug="beta", sort_order=1)

    def test_sort_order_wins_then_name(self) -> None:
        self.assertEqual(
            [s.name for s in DanceStyle.objects.all()],
            ["Beta", "Zeta", "Alpha"],
        )

    def test_str_is_the_name(self) -> None:
        self.assertEqual(str(DanceStyle.objects.get(slug="alpha")), "Alpha")


class SeasonTests(TestCase):
    """A studio season, and the guarantee that only one is ever current."""

    def test_setting_current_unsets_the_previous_one(self) -> None:
        old = Season.objects.create(label="2025/2026", slug="2025-2026", is_current=True)
        new = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)

        old.refresh_from_db()
        self.assertFalse(old.is_current)
        self.assertTrue(new.is_current)
        self.assertEqual(Season.objects.filter(is_current=True).count(), 1)

    def test_current_classmethod_returns_the_current_season(self) -> None:
        Season.objects.create(label="2025/2026", slug="2025-2026", is_current=False)
        current = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)
        self.assertEqual(Season.current(), current)

    def test_current_is_none_when_nothing_is_flagged(self) -> None:
        Season.objects.create(label="2025/2026", slug="2025-2026", is_current=False)
        self.assertIsNone(Season.current())


class TrainingLevelTests(TestCase):
    """The schedule legend is a filtered view of the levels, not a separate list."""

    @override
    def setUp(self) -> None:
        TrainingLevel.objects.create(
            name="Crew Class", slug="crew", display_label="Crew Class",
            colour_identifier="crew", sort_order=10, show_in_legend=True,
        )
        TrainingLevel.objects.create(
            name="Private", slug="private", display_label="Private",
            colour_identifier="private", sort_order=90, show_in_legend=False,
        )

    def test_legend_excludes_hidden_levels(self) -> None:
        legend = TrainingLevel.objects.filter(show_in_legend=True)
        self.assertEqual([level.slug for level in legend], ["crew"])

    def test_hidden_levels_still_exist_for_grid_colouring(self) -> None:
        self.assertTrue(TrainingLevel.objects.filter(slug="private").exists())

    def test_colour_identifier_is_semantic_not_a_hex_value(self) -> None:
        for level in TrainingLevel.objects.all():
            self.assertFalse(level.colour_identifier.startswith("#"))


class SeedCommandTests(TestCase):
    """The seed command must be safe to run repeatedly against a live database."""

    def test_seeds_every_vocabulary(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)

        self.assertEqual(Season.objects.count(), 1)
        self.assertEqual(ProgramCategory.objects.count(), 5)
        self.assertEqual(TrainingLevel.objects.count(), 9)
        self.assertEqual(DanceStyle.objects.count(), 16)
        self.assertEqual(StudioRoom.objects.count(), 2)
        self.assertEqual(EventType.objects.count(), 7)
        self.assertEqual(CalendarCategory.objects.count(), 9)

    def test_seeds_the_nine_legend_levels_including_the_two_hidden_ones(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)

        self.assertEqual(TrainingLevel.objects.filter(show_in_legend=True).count(), 7)
        self.assertEqual(TrainingLevel.objects.filter(show_in_legend=False).count(), 2)

    def test_seeds_both_studio_rooms(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        self.assertEqual(
            [room.name for room in StudioRoom.objects.all()],
            ["Notorious BIG", "Black & Yellow"],
        )

    def test_rerunning_creates_no_duplicates(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        before = DanceStyle.objects.count()

        call_command("seed_poundit_taxonomies", verbosity=0)

        self.assertEqual(DanceStyle.objects.count(), before)

    def test_rerunning_preserves_admin_edits_by_default(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        style = DanceStyle.objects.get(slug="hip-hop")
        style.short_description = "Edited by studio staff"
        style.save()

        call_command("seed_poundit_taxonomies", verbosity=0)

        style.refresh_from_db()
        self.assertEqual(style.short_description, "Edited by studio staff")

    def test_update_flag_restores_defaults(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        style = DanceStyle.objects.get(slug="hip-hop")
        style.name = "Renamed"
        style.save()

        call_command("seed_poundit_taxonomies", "--update", verbosity=0)

        style.refresh_from_db()
        self.assertEqual(style.name, "Hip Hop")

    def test_dry_run_writes_nothing(self) -> None:
        call_command("seed_poundit_taxonomies", "--dry-run", verbosity=0)
        self.assertEqual(DanceStyle.objects.count(), 0)
        self.assertEqual(TrainingLevel.objects.count(), 0)

    def test_seeded_season_is_current_and_dated(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        season = Season.current()

        self.assertIsNotNone(season)
        self.assertEqual(season.label, "2026/2027")
        self.assertEqual(season.start_date, datetime.date(2026, 9, 14))


class PounditSettingsTests(TestCase):
    """Settings are per-site, so Pound It and Alternative Naissance never collide."""

    def test_settings_resolve_for_the_site(self) -> None:
        site = Site.objects.get(is_default_site=True)
        settings_obj = PounditSettings.for_site(site)

        self.assertEqual(settings_obj.studio_name, "Pound It Hip Hop Studios")
        self.assertEqual(settings_obj.registration_cta_label, "Register")

    def test_each_site_gets_its_own_settings_row(self) -> None:
        default = Site.objects.get(is_default_site=True)
        other = Site.objects.create(
            hostname="alternative-naissance.localhost",
            port=80,
            root_page=default.root_page,
            is_default_site=False,
        )

        a = PounditSettings.for_site(default)
        a.phone_number = "(403) 896-7935"
        a.save()

        b = PounditSettings.for_site(other)

        self.assertNotEqual(a.pk, b.pk)
        self.assertEqual(b.phone_number, "")

    def test_current_season_is_optional(self) -> None:
        site = Site.objects.get(is_default_site=True)
        settings_obj = PounditSettings.for_site(site)
        self.assertIsNone(settings_obj.current_season)
