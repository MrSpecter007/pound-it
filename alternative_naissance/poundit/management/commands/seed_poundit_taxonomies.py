"""
Seed the Pound It vocabularies.

Safe to re-run. By default existing rows are left exactly as staff edited them
and only missing rows are created; pass ``--update`` to refresh existing rows
back to these defaults, or ``--dry-run`` to see what would change.

    python manage.py seed_poundit_taxonomies --dry-run
    python manage.py seed_poundit_taxonomies
"""

import datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from poundit.models import (
    CalendarCategory,
    DanceStyle,
    EventType,
    ProgramCategory,
    Season,
    StudioRoom,
    TrainingLevel,
)

SEASONS = [
    {
        "slug": "2026-2027",
        "label": "2026/2027",
        "start_date": datetime.date(2026, 9, 14),
        "end_date": datetime.date(2027, 6, 17),
        "is_current": True,
    },
]

PROGRAM_CATEGORIES = [
    {"slug": "kids-teen", "name": "Kids & Teen Rec", "sort_order": 10},
    {"slug": "adult", "name": "Adult Rec", "sort_order": 20},
    {"slug": "competitive", "name": "Competitive", "sort_order": 30},
    {"slug": "open-training", "name": "Open Training", "sort_order": 40},
    {"slug": "other", "name": "Other", "sort_order": 90},
]

# Mirrors the legend printed on the studio's own weekly schedule graphic.
# "choreography" and "private" are seeded because the grid needs them to colour
# those cells; they are hidden from the public legend by default.
TRAINING_LEVELS = [
    {
        "slug": "crew", "name": "Crew Class", "display_label": "Crew Class",
        "colour_identifier": "crew", "description": "Audition or placement crews.",
        "age_label": "", "sort_order": 10, "show_in_legend": True,
    },
    {
        "slug": "age-2-3", "name": "Ages 2-3", "display_label": "2-3 Years",
        "colour_identifier": "age-2-3", "description": "Bambinos.",
        "age_label": "Ages 2-3", "age_min": 2, "age_max": 3, "sort_order": 20, "show_in_legend": True,
    },
    {
        "slug": "age-4-5", "name": "Ages 4-5", "display_label": "4-5 Years",
        "colour_identifier": "age-4-5", "description": "",
        "age_label": "Ages 4-5", "age_min": 4, "age_max": 5, "sort_order": 30, "show_in_legend": True,
    },
    {
        "slug": "age-6-9", "name": "Ages 6-9", "display_label": "6-9 Years",
        "colour_identifier": "age-6-9", "description": "",
        "age_label": "Ages 6-9", "age_min": 6, "age_max": 9, "sort_order": 40, "show_in_legend": True,
    },
    {
        "slug": "age-10-15", "name": "Ages 10-15", "display_label": "10-15 Years",
        "colour_identifier": "age-10-15", "description": "",
        "age_label": "Ages 10-15", "age_min": 10, "age_max": 15, "sort_order": 50, "show_in_legend": True,
    },
    {
        "slug": "piba", "name": "PIBA (Adults)", "display_label": "PIBA (Adults)",
        "colour_identifier": "piba", "description": "Beginner adults.",
        "age_label": "Adults", "sort_order": 60, "show_in_legend": True,
    },
    {
        "slug": "open", "name": "Open Classes", "display_label": "Open Classes",
        "colour_identifier": "open", "description": "Drop-in and open styles.",
        "age_label": "", "sort_order": 70, "show_in_legend": True,
    },
    {
        "slug": "choreography", "name": "Choreography", "display_label": "Choreography",
        "colour_identifier": "choreography", "description": "",
        "age_label": "", "sort_order": 80, "show_in_legend": False,
    },
    {
        "slug": "private", "name": "Private", "display_label": "Private",
        "colour_identifier": "private", "description": "Private training and studio rentals.",
        "age_label": "", "sort_order": 90, "show_in_legend": False,
    },
]

# Styles printed on the source site, plus those appearing only in faculty bios.
DANCE_STYLES = [
    {"slug": "hip-hop", "name": "Hip Hop", "sort_order": 10},
    {"slug": "breaking", "name": "Breaking", "sort_order": 20},
    {"slug": "locking", "name": "Locking", "sort_order": 30},
    {"slug": "waacking", "name": "Waacking", "sort_order": 40},
    {"slug": "house", "name": "House", "sort_order": 50},
    {"slug": "litefeet", "name": "Litefeet", "sort_order": 60},
    {"slug": "dancehall", "name": "Dancehall", "sort_order": 70},
    {"slug": "choreography", "name": "Choreography", "sort_order": 80},
    {"slug": "atlanta-styles", "name": "Atlanta Styles", "sort_order": 90},
    {"slug": "jersey-club", "name": "Jersey Club", "sort_order": 100},
    {"slug": "popping", "name": "Popping", "sort_order": 110},
    {"slug": "animation", "name": "Animation", "sort_order": 120},
    {"slug": "vogue", "name": "Vogue", "sort_order": 130},
    {"slug": "afro", "name": "Afro", "sort_order": 140},
    {"slug": "freestyle", "name": "Freestyle", "sort_order": 150},
    {"slug": "campbellocking", "name": "Campbellocking", "sort_order": 160},
]

STUDIO_ROOMS = [
    {"slug": "notorious-big", "name": "Notorious BIG", "sort_order": 10},
    {"slug": "black-and-yellow", "name": "Black & Yellow", "sort_order": 20},
]

EVENT_TYPES = [
    {"slug": "battle", "name": "Battle", "sort_order": 10},
    {"slug": "workshop", "name": "Workshop", "sort_order": 20},
    {"slug": "camp", "name": "Camp", "sort_order": 30},
    {"slug": "performance", "name": "Performance", "sort_order": 40},
    {"slug": "competition", "name": "Competition", "sort_order": 50},
    {"slug": "festival", "name": "Festival", "sort_order": 60},
    {"slug": "intensive", "name": "Intensive", "sort_order": 70},
]

CALENDAR_CATEGORIES = [
    {"slug": "class", "name": "Class Day", "sort_order": 10},
    {"slug": "closure", "name": "Closure", "sort_order": 20},
    {"slug": "battle", "name": "Battle", "sort_order": 30},
    {"slug": "competition", "name": "Competition", "sort_order": 40},
    {"slug": "workshop", "name": "Workshop", "sort_order": 50},
    {"slug": "show", "name": "Show", "sort_order": 60},
    {"slug": "camp", "name": "Camp", "sort_order": 70},
    {"slug": "tryout", "name": "Tryout", "sort_order": 80},
    {"slug": "other", "name": "Other", "sort_order": 90},
]

GROUPS: list[tuple[str, Any, list[dict]]] = [
    ("Season", Season, SEASONS),
    ("Program category", ProgramCategory, PROGRAM_CATEGORIES),
    ("Training level", TrainingLevel, TRAINING_LEVELS),
    ("Dance style", DanceStyle, DANCE_STYLES),
    ("Studio room", StudioRoom, STUDIO_ROOMS),
    ("Event type", EventType, EVENT_TYPES),
    ("Calendar category", CalendarCategory, CALENDAR_CATEGORIES),
]


class Command(BaseCommand):
    help = "Create the Pound It taxonomies. Idempotent; existing rows are preserved unless --update is passed."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing anything.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Overwrite existing rows with these defaults, discarding admin edits.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        update: bool = options["update"]
        verbose: bool = options.get("verbosity", 1) >= 1

        created_total = updated_total = skipped_total = 0

        with transaction.atomic():
            for label, model, rows in GROUPS:
                for row in rows:
                    defaults = {k: v for k, v in row.items() if k != "slug"}
                    existing = model.objects.filter(slug=row["slug"]).first()

                    if existing is None:
                        created_total += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"  + {label}: {row['slug']}"))
                        if not dry_run:
                            model.objects.create(slug=row["slug"], **defaults)
                    elif update:
                        updated_total += 1
                        if verbose:
                            self.stdout.write(self.style.WARNING(f"  ~ {label}: {row['slug']}"))
                        if not dry_run:
                            for key, value in defaults.items():
                                setattr(existing, key, value)
                            existing.save()
                    else:
                        skipped_total += 1

            if dry_run:
                transaction.set_rollback(True)

        summary = f"{created_total} created, {updated_total} updated, {skipped_total} left untouched"
        if not verbose:
            return
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Pound It taxonomies seeded: {summary}"))
