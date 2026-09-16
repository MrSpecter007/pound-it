"""
Create 301s for the legacy Wix URLs.

Run after the page tree exists, since each redirect points at a live path.
Written as a command rather than a data migration for exactly that reason: a
migration runs before any content exists and would create redirects to nowhere.

    python manage.py seed_poundit_redirects --dry-run
    python manage.py seed_poundit_redirects

Re-runnable. Redirects edited in the admin are left alone unless --update.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site

from poundit.imports import URL_MAP, URL_MAP_NEEDS_CONFIRMATION


class Command(BaseCommand):
    help = "Create 301 redirects from the legacy Wix URLs to their new paths."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--update",
            action="store_true",
            help="Overwrite existing redirects, discarding admin edits.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        update: bool = options["update"]
        verbose: bool = options.get("verbosity", 1) >= 1

        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            if verbose:
                self.stderr.write(self.style.ERROR("No default site found."))
            return

        if not Page.objects.filter(slug="poundit").exists():
            if verbose:
                self.stderr.write(
                    self.style.ERROR(
                        "The Pound It page tree does not exist yet. "
                        "Run 'manage.py seed_poundit_site' first."
                    )
                )
            return

        created = updated = skipped = 0
        unresolved: list[str] = []

        with transaction.atomic():
            for legacy, destination in URL_MAP.items():
                normalised = Redirect.normalise_path(legacy)
                existing = Redirect.objects.filter(old_path=normalised, site=site).first()

                if existing is not None and not update:
                    skipped += 1
                    continue

                if not self._destination_exists(destination):
                    unresolved.append(f"{legacy} -> {destination}")

                if existing is not None:
                    updated += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f"  ~ {legacy} -> {destination}")
                        )
                    if not dry_run:
                        existing.redirect_link = destination
                        existing.is_permanent = True
                        existing.save()
                    continue

                created += 1
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"  + {legacy} -> {destination}"))
                if not dry_run:
                    Redirect.objects.create(
                        old_path=normalised,
                        site=site,
                        redirect_link=destination,
                        is_permanent=True,
                    )

            if dry_run:
                transaction.set_rollback(True)

        if not verbose:
            return

        summary = f"{created} created, {updated} updated, {skipped} left untouched"
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Legacy redirects: {summary}"))

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Needs a human decision:"))
        for legacy in URL_MAP_NEEDS_CONFIRMATION:
            self.stdout.write(
                f"  - {legacy} -> {URL_MAP[legacy]} is an inference, not a mapping the source "
                "site states. Confirm or change it."
            )
        if unresolved:
            self.stdout.write(
                "  - These destinations did not resolve to a live page. Check the tree:"
            )
            for item in unresolved:
                self.stdout.write(f"      {item}")

    def _destination_exists(self, destination: str) -> bool:
        """Cheap sanity check that the target path is actually served."""
        path = destination.split("?")[0].strip("/")
        if not path:
            return True
        segments = path.split("/")

        # A page path, or a routable subpath one level below a page.
        for depth in (len(segments), len(segments) - 1):
            if depth <= 0:
                continue
            if Page.objects.filter(slug=segments[depth - 1], live=True).exists():
                return True
        return False
