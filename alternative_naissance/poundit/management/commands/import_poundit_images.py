"""
Import images from a local folder into Wagtail and attach them.

Nothing here touches the Wix CDN. The files are supplied locally — the studio
owns them — and this imports them into Wagtail's own image library so published
pages never depend on the old host.

    python manage.py import_poundit_images --list
    python manage.py import_poundit_images --source-dir /path/to/images --dry-run
    python manage.py import_poundit_images --source-dir /path/to/images

Re-runnable. Files already imported are matched by content hash, so re-running
attaches the existing image rather than creating a second copy of it.
"""

from pathlib import Path
from typing import Any

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images import get_image_model
from wagtail.models import Site
from wagtail.utils.file import hash_filelike

from poundit.imports import AMBIGUOUS_IMAGES, IMAGE_SOURCES, IMAGES_NOT_AVAILABLE
from poundit.models import FacultyMember, ImportedObject, ImportStatus, PounditSettings

ACCEPTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


def _normalise(name: str) -> str:
    """Lowercase, letters and digits only, so 'Pound It Logo' becomes 'pounditlogo'."""
    return "".join(character for character in name.lower() if character.isalnum())


def file_hash(path: Path) -> str:
    """
    Hash exactly the way Wagtail does.

    Rolling our own would produce a digest that never matches ``Image.file_hash``,
    so deduplication would silently do nothing.
    """
    with path.open("rb") as handle:
        return hash_filelike(handle)


class Command(BaseCommand):
    help = "Import Pound It images from a local folder and attach them to faculty and settings."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--source-dir",
            default=None,
            help="Folder holding the image files.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            dest="list_only",
            help="Print the files this command expects and where each came from.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")

    def handle(self, *args: Any, **options: Any) -> None:
        verbose: bool = options.get("verbosity", 1) >= 1

        if options["list_only"]:
            self._print_manifest()
            return

        source_dir = options["source_dir"]
        if not source_dir:
            self.stderr.write(
                self.style.ERROR(
                    "Pass --source-dir with the folder holding the images, "
                    "or --list to see what is expected."
                )
            )
            return

        directory = Path(source_dir)
        if not directory.is_dir():
            self.stderr.write(self.style.ERROR(f"Not a directory: {directory}"))
            return

        dry_run: bool = options["dry_run"]
        Image = get_image_model()

        imported = attached = reused = missing = 0
        missing_stems: list[str] = []
        used_files: set[Path] = set()

        with transaction.atomic():
            for spec in IMAGE_SOURCES:
                path = self._find_file(directory, spec["stem"], spec.get("aliases", []))
                if path is None:
                    missing += 1
                    missing_stems.append(spec["stem"])
                    ImportedObject.record(
                        source_identifier=f"image:{spec['stem']}",
                        source_url=spec["source_url"],
                        status=ImportStatus.PENDING,
                        notes=f"No file named {spec['stem']}.* found in {directory}.",
                    )
                    continue

                used_files.add(path)
                digest = file_hash(path)
                image = Image.objects.filter(file_hash=digest).first()

                if image is not None:
                    reused += 1
                    if verbose:
                        self.stdout.write(f"    {spec['stem']}: already in the library")
                else:
                    imported += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"  + {spec['stem']}: {path.name}"))
                    if not dry_run:
                        with path.open("rb") as handle:
                            image = Image(
                                title=spec["title"],
                                description=spec.get("description", ""),
                                file=ImageFile(handle, name=path.name),
                            )
                            image.save()
                        # Wagtail fills file_hash lazily. Force it now, or the
                        # next run has nothing to match against.
                        image.get_file_hash()

                if dry_run or image is None:
                    continue

                if self._attach(spec, image):
                    attached += 1

                ImportedObject.record(
                    source_identifier=f"image:{spec['stem']}",
                    target=image,
                    source_url=spec["source_url"],
                    status=ImportStatus.IMPORTED,
                    notes="Needs a human eye: two portraits share a source filename."
                    if spec["stem"] in AMBIGUOUS_IMAGES
                    else "",
                )

            for slug, note in IMAGES_NOT_AVAILABLE:
                ImportedObject.record(
                    source_identifier=f"image:{slug}",
                    status=ImportStatus.SKIPPED,
                    notes=note,
                )

            if dry_run:
                transaction.set_rollback(True)

        if not verbose:
            return

        summary = (
            f"{imported} imported, {reused} already in the library, "
            f"{attached} attached, {missing} missing"
        )
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Images: {summary}"))

        if missing_stems:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("No file supplied for:"))
            for stem in missing_stems:
                self.stdout.write(f"  - {stem}")

        leftovers = self._unmatched(directory, used_files)
        if leftovers:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR("In the folder but matched no key, so NOT imported:")
            )
            for path in leftovers:
                self.stdout.write(f"  - {path.name}")
            self.stdout.write(
                "    Rename to one of the keys above, or add it to IMAGE_SOURCES."
            )

        if AMBIGUOUS_IMAGES:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Needs a human decision:"))
            self.stdout.write(
                "  - The portraits for "
                + " and ".join(AMBIGUOUS_IMAGES)
                + " resolve to the same source filename on the old host. Confirm they are "
                "different people before publishing."
            )
            self.stdout.write(
                "  - Alt text is written from what the source page showed. Reword anything "
                "that does not describe the image accurately."
            )

    def _find_file(
        self, directory: Path, stem: str, aliases: list[str] | None = None
    ) -> Path | None:
        """
        Match a supplied file to an expected key.

        People name files the way people do: "Allen.jpeg", "Pound It Logo.jpeg".
        Case, spaces and punctuation are ignored, and a key is accepted at either
        end of the name, so "Pound It Logo" answers to "logo".

        Anything looser would start guessing, and guessing here attaches the
        wrong person's face to a profile. Misspellings that have actually turned
        up are listed explicitly as ``aliases`` instead.
        """
        targets = [_normalise(stem)] + [_normalise(alias) for alias in (aliases or [])]

        candidates = [
            path
            for path in sorted(directory.iterdir())
            if path.is_file() and path.suffix.lower() in ACCEPTED_SUFFIXES
        ]

        for path in candidates:
            if _normalise(path.stem) in targets:
                return path

        for path in candidates:
            name = _normalise(path.stem)
            if any(name.startswith(t) or name.endswith(t) for t in targets):
                return path

        return None

    def _unmatched(self, directory: Path, used: set[Path]) -> list[Path]:
        """Files sitting in the folder that answered to no key."""
        return [
            path
            for path in sorted(directory.iterdir())
            if path.is_file()
            and path.suffix.lower() in ACCEPTED_SUFFIXES
            and path not in used
        ]

    def _attach(self, spec: dict, image) -> bool:
        """Put the image where it belongs. Never overwrites one already set."""
        if spec["target"] == "faculty":
            member = FacultyMember.objects.filter(slug=spec["slug"]).first()
            if member is None or member.portrait_id:
                return False
            member.portrait = image
            member.save()
            return True

        if spec["target"] == "settings":
            site = Site.objects.filter(is_default_site=True).first()
            if site is None:
                return False
            studio_settings = PounditSettings.for_site(site)
            field = spec.get("field", "logo")
            if getattr(studio_settings, f"{field}_id", None):
                return False
            setattr(studio_settings, field, image)
            studio_settings.save()
            return True

        return False

    def _print_manifest(self) -> None:
        self.stdout.write("Save each file into one folder, named by its key below.")
        self.stdout.write("Any of .jpg .jpeg .png .webp .gif .avif will do.")
        self.stdout.write("")
        for spec in IMAGE_SOURCES:
            flag = "  <- shares a source filename, check it" if spec["stem"] in AMBIGUOUS_IMAGES else ""
            also = spec.get("aliases")
            alias_note = f" (also accepts {', '.join(also)})" if also else ""
            self.stdout.write(f"  {spec['stem']}.*{alias_note}  {spec['title']}{flag}")
            self.stdout.write(f"      from {spec['source_url']}")
        if IMAGES_NOT_AVAILABLE:
            self.stdout.write("")
            self.stdout.write("No portrait published on the source site:")
            for slug, note in IMAGES_NOT_AVAILABLE:
                self.stdout.write(f"  {slug} - {note}")
