"""
Run the whole Pound It import in order, and record what came from where.

This is the single entry point the brief asks for. It runs the individual seeds
— each of which stays runnable on its own — and then reconciles the ledger so
every imported object can be traced back to a page on the old site.

    python manage.py import_poundit --dry-run
    python manage.py import_poundit
    python manage.py import_poundit --no-default-site

Re-runnable: the seeds create nothing twice, and the ledger is upserted.
"""

from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from poundit.imports import SOURCE_URLS
from poundit.models import (
    CalendarEntry,
    FacultyMember,
    ImportedObject,
    ImportStatus,
    Program,
)

STEPS = [
    ("seed_poundit_taxonomies", "Vocabularies"),
    ("seed_poundit_schedule", "Programs and weekly schedule"),
    ("seed_poundit_faculty", "Faculty and session instructors"),
    ("seed_poundit_calendar", "Season calendar"),
    ("seed_poundit_site", "Page tree and settings"),
    ("seed_poundit_redirects", "Legacy URL redirects"),
]


class Command(BaseCommand):
    help = "Import Pound It from the source site and record the source mapping."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--no-default-site",
            action="store_true",
            help="Build the tree but leave the existing default site alone.",
        )
        parser.add_argument(
            "--skip-seeds",
            action="store_true",
            help="Only reconcile the ledger against what is already in the database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        verbose: bool = options.get("verbosity", 1) >= 1
        step_verbosity = 1 if verbose else 0

        if not options["skip_seeds"]:
            for command, label in STEPS:
                if verbose:
                    self.stdout.write(self.style.MIGRATE_HEADING(f"\n{label}"))
                kwargs: dict[str, Any] = {"verbosity": step_verbosity}
                if dry_run:
                    kwargs["dry_run"] = True
                if command == "seed_poundit_site" and options["no_default_site"]:
                    kwargs["no_default_site"] = True
                call_command(command, **kwargs)

        if dry_run:
            if verbose:
                self.stdout.write(
                    self.style.NOTICE("\nDry run - the ledger was not written.")
                )
            return

        recorded = self._record_ledger()

        if verbose:
            self.stdout.write(self.style.MIGRATE_HEADING("\nSource mapping"))
            self.stdout.write(
                self.style.SUCCESS(f"{recorded} ledger entries recorded.")
            )
            self.stdout.write(
                "Review them in the Wagtail admin under Import ledger, or with "
                "'manage.py import_poundit --skip-seeds' to refresh."
            )
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Images are not fetched from the old host. Run "
                    "'manage.py import_poundit_images --list' for what to supply."
                )
            )

    def _record_ledger(self) -> int:
        """Trace every imported object back to the page it came from."""
        count = 0

        with transaction.atomic():
            for program in Program.objects.select_related("category"):
                category_slug = program.category.slug if program.category else "other"
                ImportedObject.record(
                    source_identifier=f"program:{program.slug}",
                    target=program,
                    source_url=SOURCE_URLS.get(category_slug, SOURCE_URLS["schedule"]),
                    status=ImportStatus.IMPORTED,
                    notes=""
                    if program.is_public
                    else "Schedule occupancy, not a public offering.",
                )
                count += 1

            for member in FacultyMember.objects.all():
                ImportedObject.record(
                    source_identifier=f"faculty:{member.slug}",
                    target=member,
                    source_url=SOURCE_URLS["faculty"],
                    status=ImportStatus.NEEDS_REVIEW
                    if not member.full_bio
                    else ImportStatus.IMPORTED,
                    notes="Biography still to be pasted in verbatim."
                    if not member.full_bio
                    else "",
                )
                count += 1

            for entry in CalendarEntry.objects.all():
                ImportedObject.record(
                    source_identifier=f"calendar:{entry.start_date}:{entry.title[:80]}",
                    target=entry,
                    source_url=SOURCE_URLS["important-dates"],
                    status=ImportStatus.NEEDS_REVIEW
                    if entry.is_tentative
                    else ImportStatus.IMPORTED,
                    notes="Published as tentative on the source site."
                    if entry.is_tentative
                    else "",
                )
                count += 1

        return count
