"""
Seed the 2026/2027 season calendar.

Transcribed from the Important Dates page on pounditdj.com, which publishes the
season under the heading "2026-2027 Tentative Dates". Every entry is therefore
seeded with ``is_tentative`` set; clear the flag per row as dates are confirmed.

Wording is copied as published. Nothing here rewrites the studio's own text.

    python manage.py seed_poundit_calendar --dry-run
    python manage.py seed_poundit_calendar
"""

import datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from poundit.models import CalendarCategory, CalendarEntry, Season


def d(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value)


# (title as published, start, end or None, category slug)
ENTRIES: list[tuple[str, str, str | None, str]] = [
    ("First day of fall classes", "2026-09-14", None, "class"),
    ("Closed for Truth and Reconciliation Day", "2026-09-30", None, "closure"),
    ("Closed for Thanksgiving", "2026-10-09", "2026-10-12", "closure"),
    ("Halloween Battle", "2026-10-30", None, "battle"),
    ("Closed for Halloween", "2026-10-31", None, "closure"),
    ("Closed for fall break / Observe Remembrance Day", "2026-11-09", "2026-11-11", "closure"),
    ("Christmas Battle", "2026-11-28", None, "battle"),
    ("Christmas Break", "2026-12-21", "2027-01-03", "closure"),
    ("Classes Resume", "2027-01-04", None, "class"),
    ("Closed for Winter Break", "2027-02-15", "2027-02-19", "closure"),
    ("Closed for Easter", "2027-03-26", "2027-03-29", "closure"),
    ("Spring Training Camp with Boss Fam", "2027-03-30", "2027-04-02", "camp"),
    ("Zona Central", "2027-04-03", None, "competition"),
    ("Closed for May Long Weekend", "2027-05-21", "2027-05-24", "closure"),
    ("Year End Show", "2027-06-11", None, "show"),
    ("Bring a friend to dance and last day of class", "2027-06-17", None, "class"),
    ("Heat the Streets Steinbach Manitoba", "2027-06-19", None, "competition"),
    ("One For Then City Edmonton", "2027-06-26", "2027-06-27", "competition"),
    ("Pound It Family Campout", "2027-07-02", "2027-07-04", "camp"),
    ("Competitive Try Outs", "2027-07-10", None, "tryout"),
]

REVIEW_NOTES = [
    "Every entry is flagged tentative, matching the source heading "
    "'2026-2027 Tentative Dates'. Clear the flag per row once confirmed.",
    "Titles are copied verbatim, including 'One For Then City Edmonton', which reads "
    "like a typo for 'One For The City'. Left as published - correct it in the admin if intended.",
    "The last three entries fall in July 2027, after the season's end date of 17 June 2027. "
    "They are still attached to the 2026/2027 season.",
    "None of these are linked to an event page yet. Link the battles, competitions, camps and "
    "the year end show once their event pages exist.",
]


class Command(BaseCommand):
    help = "Seed the 2026/2027 season calendar. Idempotent."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument("--season", default=None, help="Season slug. Defaults to the current season.")

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        verbose: bool = options.get("verbosity", 1) >= 1

        season = (
            Season.objects.filter(slug=options["season"]).first()
            if options["season"]
            else Season.current()
        )
        if season is None:
            if verbose:
                self.stderr.write(
                    self.style.ERROR(
                        "No season found. Run 'manage.py seed_poundit_taxonomies' first."
                    )
                )
            return

        categories = {c.slug: c for c in CalendarCategory.objects.all()}
        created = skipped = 0

        with transaction.atomic():
            for title, start, end, category_slug in ENTRIES:
                existing = CalendarEntry.objects.filter(
                    title=title, start_date=d(start), season=season
                ).first()
                if existing is not None:
                    skipped += 1
                    continue

                created += 1
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"  + {start}  {title}"))
                if not dry_run:
                    CalendarEntry.objects.create(
                        title=title,
                        start_date=d(start),
                        end_date=d(end) if end else None,
                        category=categories.get(category_slug),
                        season=season,
                        is_tentative=True,
                    )

            if dry_run:
                transaction.set_rollback(True)

        if not verbose:
            return

        summary = f"{created} created, {skipped} already present"
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Season calendar seeded for {season.label}: {summary}"))

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Needs a human decision:"))
        for note in REVIEW_NOTES:
            self.stdout.write(f"  - {note}")
