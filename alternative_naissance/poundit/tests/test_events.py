"""
Tests for events and the season calendar.

The load-bearing requirement here is that a finished event leaves "upcoming" on
its own. The awkward case is a multi-day camp partway through: it has started,
it has not finished, and it must still be listed.
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
    EventIndexPage,
    EventPage,
    EventStatus,
    EventType,
    Season,
)


def _dt(days: int, hour: int = 19) -> datetime.datetime:
    return timezone.now().replace(hour=hour, minute=0, second=0, microsecond=0) + datetime.timedelta(
        days=days
    )


class EventUpcomingTests(TestCase):
    """Upcoming and past are derived, never curated by hand."""

    @override
    def setUp(self) -> None:
        # Under the site root, not the tree root, so the page actually routes.
        site_root = Site.objects.get(is_default_site=True).root_page
        self.index = EventIndexPage(title="Events", slug="events")
        site_root.add_child(instance=self.index)

        self.battle_type = EventType.objects.create(name="Battle", slug="battle")
        self.camp_type = EventType.objects.create(name="Camp", slug="camp")

    def _event(self, title: str, start, end=None, **kwargs) -> EventPage:
        event = EventPage(
            title=title,
            slug=title.lower().replace(" ", "-"),
            start_datetime=start,
            end_datetime=end,
            **kwargs,
        )
        self.index.add_child(instance=event)
        event.save_revision().publish()
        return event

    def test_future_event_is_upcoming(self) -> None:
        event = self._event("Halloween Battle", _dt(30))
        self.assertIn(event, EventPage.objects.upcoming())

    def test_finished_event_drops_out_of_upcoming(self) -> None:
        event = self._event("Last Year Battle", _dt(-30))
        self.assertNotIn(event, EventPage.objects.upcoming())
        self.assertIn(event, EventPage.objects.past())

    def test_multi_day_event_in_progress_is_still_upcoming(self) -> None:
        """A four-day camp on day two has started but has not finished."""
        camp = self._event("Spring Camp", _dt(-1), _dt(2), event_type=self.camp_type)

        self.assertIn(camp, EventPage.objects.upcoming())
        self.assertNotIn(camp, EventPage.objects.past())

    def test_multi_day_event_drops_out_only_after_its_end(self) -> None:
        camp = self._event("Old Camp", _dt(-10), _dt(-7))

        self.assertNotIn(camp, EventPage.objects.upcoming())
        self.assertIn(camp, EventPage.objects.past())

    def test_cancelled_events_are_never_upcoming(self) -> None:
        event = self._event("Cancelled Battle", _dt(20), status=EventStatus.CANCELLED)
        self.assertNotIn(event, EventPage.objects.upcoming())

    def test_sold_out_events_remain_upcoming(self) -> None:
        event = self._event("Sold Out Battle", _dt(20), status=EventStatus.SOLD_OUT)
        self.assertIn(event, EventPage.objects.upcoming())

    def test_unpublished_events_are_excluded(self) -> None:
        event = self._event("Draft Battle", _dt(20))
        event.unpublish()
        self.assertNotIn(event, EventPage.objects.upcoming())

    def test_upcoming_is_ordered_soonest_first(self) -> None:
        later = self._event("Later", _dt(60))
        sooner = self._event("Sooner", _dt(10))

        self.assertEqual(list(EventPage.objects.upcoming()), [sooner, later])

    def test_past_is_ordered_most_recent_first(self) -> None:
        older = self._event("Older", _dt(-60))
        recent = self._event("Recent", _dt(-10))

        self.assertEqual(list(EventPage.objects.past()), [recent, older])

    def test_featured_is_a_subset_of_upcoming(self) -> None:
        featured = self._event("Featured", _dt(10), featured=True)
        self._event("Not featured", _dt(20))
        self._event("Featured but past", _dt(-10), featured=True)

        self.assertEqual(list(EventPage.objects.featured()), [featured])

    def test_of_type_filters_by_slug_or_instance(self) -> None:
        battle = self._event("Battle", _dt(10), event_type=self.battle_type)
        self._event("Camp", _dt(20), event_type=self.camp_type)

        self.assertEqual(list(EventPage.objects.upcoming().of_type("battle")), [battle])
        self.assertEqual(list(EventPage.objects.upcoming().of_type(self.battle_type)), [battle])


class EventDisplayTests(TestCase):
    @override
    def setUp(self) -> None:
        # Under the site root, not the tree root, so the page actually routes.
        site_root = Site.objects.get(is_default_site=True).root_page
        self.index = EventIndexPage(title="Events", slug="events")
        site_root.add_child(instance=self.index)

    def _event(self, **kwargs) -> EventPage:
        event = EventPage(title="Event", slug="event", **kwargs)
        self.index.add_child(instance=event)
        return event

    def test_single_day_date_display(self) -> None:
        event = self._event(start_datetime=timezone.make_aware(datetime.datetime(2027, 4, 3, 19)))
        self.assertEqual(event.date_display, "3 April 2027")

    def test_same_month_range_collapses_the_month(self) -> None:
        event = self._event(
            start_datetime=timezone.make_aware(datetime.datetime(2027, 6, 26, 10)),
            end_datetime=timezone.make_aware(datetime.datetime(2027, 6, 27, 18)),
        )
        self.assertEqual(event.date_display, "26 - 27 June 2027")

    def test_cross_month_range_names_both_months(self) -> None:
        event = self._event(
            start_datetime=timezone.make_aware(datetime.datetime(2027, 3, 30, 10)),
            end_datetime=timezone.make_aware(datetime.datetime(2027, 4, 2, 18)),
        )
        self.assertEqual(event.date_display, "30 March - 2 April 2027")

    def test_same_day_end_time_is_not_multi_day(self) -> None:
        event = self._event(
            start_datetime=timezone.make_aware(datetime.datetime(2027, 4, 3, 19)),
            end_datetime=timezone.make_aware(datetime.datetime(2027, 4, 3, 23)),
        )
        self.assertFalse(event.is_multi_day)
        self.assertEqual(event.date_display, "3 April 2027")

    def test_price_text_wins_over_an_amount(self) -> None:
        event = self._event(
            start_datetime=_dt(10),
            price_amount=Decimal("20"),
            price_text="$20 spectator / $35 competitor",
        )
        self.assertEqual(event.price_display, "$20 spectator / $35 competitor")

    def test_price_amount_drops_trailing_zeros(self) -> None:
        event = self._event(start_datetime=_dt(10), price_amount=Decimal("20.00"))
        self.assertEqual(event.price_display, "$20")

    def test_price_display_is_empty_when_unpriced(self) -> None:
        self.assertEqual(self._event(start_datetime=_dt(10)).price_display, "")


class EventIndexContextTests(TestCase):
    @override
    def setUp(self) -> None:
        # Under the site root, not the tree root, so the page actually routes.
        site_root = Site.objects.get(is_default_site=True).root_page
        self.index = EventIndexPage(title="Events", slug="events")
        site_root.add_child(instance=self.index)
        self.workshop = EventType.objects.create(name="Workshop", slug="workshop")

    def test_context_exposes_upcoming_past_and_types(self) -> None:
        response = self.client.get(self.index.url)

        self.assertEqual(response.status_code, 200)
        for key in ("upcoming", "past", "featured", "event_types", "active_type"):
            self.assertIn(key, response.context)

    def test_type_filter_narrows_the_listing(self) -> None:
        response = self.client.get(f"{self.index.url}?type=workshop")

        self.assertEqual(response.context["active_type"], "workshop")


class CalendarEntryTests(TestCase):
    @override
    def setUp(self) -> None:
        self.season = Season.objects.create(label="2026/2027", slug="2026-2027", is_current=True)
        self.closure = CalendarCategory.objects.create(name="Closure", slug="closure")

    def _entry(self, title: str, start: str, end: str | None = None, **kwargs) -> CalendarEntry:
        return CalendarEntry.objects.create(
            title=title,
            start_date=datetime.date.fromisoformat(start),
            end_date=datetime.date.fromisoformat(end) if end else None,
            season=self.season,
            category=self.closure,
            **kwargs,
        )

    def test_entries_sort_chronologically_by_default(self) -> None:
        self._entry("Later", "2027-01-04")
        self._entry("Earlier", "2026-09-14")

        self.assertEqual(
            [e.title for e in CalendarEntry.objects.all()], ["Earlier", "Later"]
        )

    def test_single_day_display(self) -> None:
        self.assertEqual(self._entry("A", "2026-09-14").date_display, "14 September 2026")

    def test_same_month_range_display(self) -> None:
        self.assertEqual(
            self._entry("A", "2026-10-09", "2026-10-12").date_display, "9-12 October 2026"
        )

    def test_cross_year_range_display(self) -> None:
        self.assertEqual(
            self._entry("A", "2026-12-21", "2027-01-03").date_display,
            "21 December 2026 - 3 January 2027",
        )

    def test_by_month_groups_in_order(self) -> None:
        self._entry("Sept", "2026-09-14")
        self._entry("Oct", "2026-10-09", "2026-10-12")
        self._entry("Also Sept", "2026-09-30")

        grouped = CalendarEntry.objects.for_season(self.season).by_month()
        months = list(grouped.keys())

        self.assertEqual(months[0], datetime.date(2026, 9, 1))
        self.assertEqual(len(grouped[months[0]]), 2)

    def test_multi_day_entry_stays_upcoming_until_it_ends(self) -> None:
        today = timezone.localdate()
        entry = CalendarEntry.objects.create(
            title="Break",
            start_date=today - datetime.timedelta(days=2),
            end_date=today + datetime.timedelta(days=2),
            season=self.season,
        )
        self.assertIn(entry, CalendarEntry.objects.upcoming())
        self.assertNotIn(entry, CalendarEntry.objects.past())

    def test_of_category_filters_by_slug(self) -> None:
        entry = self._entry("Closed", "2026-10-31")
        self.assertEqual(list(CalendarEntry.objects.of_category("closure")), [entry])

    def test_for_season_with_no_season_is_empty(self) -> None:
        self._entry("A", "2026-09-14")
        self.assertEqual(list(CalendarEntry.objects.for_season(None)), [])


class CalendarSeedCommandTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)

    def test_seeds_the_whole_published_season(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertEqual(CalendarEntry.objects.count(), 20)

    def test_every_entry_is_marked_tentative(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertEqual(CalendarEntry.objects.filter(is_tentative=True).count(), 20)

    def test_titles_are_copied_verbatim_including_the_apparent_typo(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertTrue(
            CalendarEntry.objects.filter(title="One For Then City Edmonton").exists()
        )

    def test_multi_day_entries_keep_their_end_date(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        christmas = CalendarEntry.objects.get(title="Christmas Break")

        self.assertEqual(christmas.start_date, datetime.date(2026, 12, 21))
        self.assertEqual(christmas.end_date, datetime.date(2027, 1, 3))
        self.assertTrue(christmas.is_multi_day)

    def test_categories_are_relations_not_strings(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertEqual(
            CalendarEntry.objects.get(title="Halloween Battle").category_slug, "battle"
        )
        self.assertEqual(CalendarEntry.objects.of_category("closure").count(), 8)

    def test_rerunning_creates_no_duplicates(self) -> None:
        call_command("seed_poundit_calendar", verbosity=0)
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertEqual(CalendarEntry.objects.count(), 20)

    def test_dry_run_writes_nothing(self) -> None:
        call_command("seed_poundit_calendar", "--dry-run", verbosity=0)
        self.assertEqual(CalendarEntry.objects.count(), 0)

    def test_command_refuses_without_a_season(self) -> None:
        Season.objects.all().delete()
        call_command("seed_poundit_calendar", verbosity=0)
        self.assertEqual(CalendarEntry.objects.count(), 0)
