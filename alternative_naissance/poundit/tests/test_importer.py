"""
Tests for the import ledger and the image pipeline.

Two properties matter most: running the importer twice must not duplicate
anything, and the same image file supplied twice must not become two library
entries. Everything the importer is unsure about has to stay visible rather
than being quietly skipped.
"""

import tempfile
from pathlib import Path
from typing import override

from django.core.management import call_command
from django.test import TestCase
from PIL import Image as PILImage
from wagtail.images import get_image_model
from wagtail.models import Site

from poundit.imports import IMAGE_SOURCES, URL_MAP
from poundit.models import (
    CalendarEntry,
    FacultyMember,
    ImportedObject,
    ImportStatus,
    PounditSettings,
    Program,
)

Image = get_image_model()


def write_image(directory: Path, name: str, colour: tuple[int, int, int]) -> Path:
    path = directory / name
    PILImage.new("RGB", (60, 60), colour).save(path)
    return path


class ImportLedgerTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)
        call_command("seed_poundit_calendar", verbosity=0)

    def test_ledger_covers_programs_faculty_and_calendar(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        expected = (
            Program.objects.count()
            + FacultyMember.objects.count()
            + CalendarEntry.objects.count()
        )
        self.assertEqual(ImportedObject.objects.count(), expected)

    def test_every_entry_traces_back_to_a_source_page(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        for entry in ImportedObject.objects.all():
            with self.subTest(entry=entry.source_identifier):
                self.assertTrue(entry.source_url.startswith("https://www.pounditdj.com"))

    def test_programs_map_to_the_crew_page_they_came_from(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="program:la-familia")
        self.assertEqual(entry.source_url, "https://www.pounditdj.com/competitivecrews")

    def test_ledger_points_at_the_real_object(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="faculty:rico")
        self.assertEqual(entry.target, FacultyMember.objects.get(slug="rico"))

    def test_faculty_without_a_bio_are_flagged_for_review(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="faculty:rico")
        self.assertEqual(entry.import_status, ImportStatus.NEEDS_REVIEW)
        self.assertIn("verbatim", entry.notes)

    def test_a_completed_bio_clears_the_review_flag(self) -> None:
        member = FacultyMember.objects.get(slug="rico")
        member.full_bio = "<p>Pasted from the source site.</p>"
        member.save()

        call_command("import_poundit", "--skip-seeds", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="faculty:rico")
        self.assertEqual(entry.import_status, ImportStatus.IMPORTED)

    def test_tentative_dates_are_flagged_for_review(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        flagged = ImportedObject.objects.filter(
            source_identifier__startswith="calendar:",
            import_status=ImportStatus.NEEDS_REVIEW,
        )
        self.assertEqual(flagged.count(), 20)

    def test_non_offerings_are_noted_as_such(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="program:studio-rentals")
        self.assertIn("not a public offering", entry.notes)

    def test_rerunning_updates_rather_than_duplicates(self) -> None:
        call_command("import_poundit", "--skip-seeds", verbosity=0)
        before = ImportedObject.objects.count()

        call_command("import_poundit", "--skip-seeds", verbosity=0)

        self.assertEqual(ImportedObject.objects.count(), before)

    def test_full_import_is_idempotent(self) -> None:
        call_command("import_poundit", verbosity=0)
        programs = Program.objects.count()
        ledger = ImportedObject.objects.count()

        call_command("import_poundit", verbosity=0)

        self.assertEqual(Program.objects.count(), programs)
        self.assertEqual(ImportedObject.objects.count(), ledger)

    def test_dry_run_writes_no_ledger(self) -> None:
        call_command("import_poundit", "--dry-run", verbosity=0)
        self.assertEqual(ImportedObject.objects.count(), 0)


class ImageImportTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

        self._tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_imports_supplied_files_and_attaches_them(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        write_image(self.directory, "cody.jpg", (40, 200, 40))

        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertEqual(Image.objects.count(), 2)
        self.assertIsNotNone(FacultyMember.objects.get(slug="rico").portrait)
        self.assertIsNotNone(FacultyMember.objects.get(slug="cody").portrait)

    def test_alt_text_is_written(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        image = FacultyMember.objects.get(slug="rico").portrait
        self.assertEqual(image.title, "Rico")
        self.assertIn("studio owner", image.description)

    def test_any_accepted_extension_works(self) -> None:
        write_image(self.directory, "rico.png", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertIsNotNone(FacultyMember.objects.get(slug="rico").portrait)

    def test_filenames_are_matched_case_insensitively(self) -> None:
        write_image(self.directory, "Rico.jpeg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertIsNotNone(FacultyMember.objects.get(slug="rico").portrait)

    def test_a_key_is_found_inside_a_longer_name(self) -> None:
        """People name files 'Pound It Logo.jpeg', not 'logo.jpeg'."""
        write_image(self.directory, "Pound It Logo.jpeg", (10, 10, 10))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        site = Site.objects.get(is_default_site=True)
        self.assertIsNotNone(PounditSettings.for_site(site).logo)

    def test_a_confirmed_misspelling_is_accepted_as_an_alias(self) -> None:
        """The studio files Cody's portrait as "Cory". Confirmed the same person."""
        write_image(self.directory, "Cory.jpeg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertIsNotNone(FacultyMember.objects.get(slug="cody").portrait)

    def test_an_unconfirmed_near_miss_is_never_guessed_at(self) -> None:
        """Guessing here attaches the wrong person's face to a profile."""
        write_image(self.directory, "Ricco.jpeg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertIsNone(FacultyMember.objects.get(slug="rico").portrait)

    def test_unrecognised_files_are_reported_not_ignored(self) -> None:
        from io import StringIO

        write_image(self.directory, "Mystery Person.jpeg", (200, 40, 40))
        out = StringIO()
        call_command("import_poundit_images", f"--source-dir={self.directory}", stdout=out)

        self.assertIn("matched no key", out.getvalue())
        self.assertIn("Mystery Person.jpeg", out.getvalue())

    def test_identical_files_are_deduplicated(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        write_image(self.directory, "cody.jpg", (200, 40, 40))  # byte-identical

        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertEqual(Image.objects.count(), 1)
        rico = FacultyMember.objects.get(slug="rico")
        cody = FacultyMember.objects.get(slug="cody")
        self.assertEqual(rico.portrait_id, cody.portrait_id)

    def test_rerunning_creates_no_second_copy(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        self.assertEqual(Image.objects.count(), 1)

    def test_an_existing_portrait_is_never_overwritten(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        chosen = Image.objects.create(title="Chosen by hand", file="chosen.jpg", width=1, height=1)
        member = FacultyMember.objects.get(slug="rico")
        member.portrait = chosen
        member.save()

        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        member.refresh_from_db()
        self.assertEqual(member.portrait_id, chosen.id)

    def test_logo_lands_in_site_settings(self) -> None:
        write_image(self.directory, "logo.png", (10, 10, 10))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        site = Site.objects.get(is_default_site=True)
        self.assertIsNotNone(PounditSettings.for_site(site).logo)

    def test_missing_files_are_recorded_as_pending(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        pending = ImportedObject.objects.filter(
            source_identifier__startswith="image:", import_status=ImportStatus.PENDING
        )
        self.assertEqual(pending.count(), len(IMAGE_SOURCES) - 1)

    def test_faculty_with_no_published_portrait_are_recorded_as_skipped(self) -> None:
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        for slug in ("breton", "genie"):
            entry = ImportedObject.objects.get(source_identifier=f"image:{slug}")
            self.assertEqual(entry.import_status, ImportStatus.SKIPPED)

    def test_ambiguous_portraits_carry_a_warning(self) -> None:
        write_image(self.directory, "nathan.jpg", (1, 2, 3))
        call_command("import_poundit_images", f"--source-dir={self.directory}", verbosity=0)

        entry = ImportedObject.objects.get(source_identifier="image:nathan")
        self.assertIn("share a source filename", entry.notes)

    def test_dry_run_imports_nothing(self) -> None:
        write_image(self.directory, "rico.jpg", (200, 40, 40))
        call_command(
            "import_poundit_images", f"--source-dir={self.directory}", "--dry-run", verbosity=0
        )

        self.assertEqual(Image.objects.count(), 0)
        self.assertIsNone(FacultyMember.objects.get(slug="rico").portrait)

    def test_a_bad_directory_is_reported_not_raised(self) -> None:
        call_command("import_poundit_images", "--source-dir=/nope/not/here", verbosity=0)
        self.assertEqual(Image.objects.count(), 0)


class UrlMapTests(TestCase):
    """The map Phase 8 will turn into redirects."""

    def test_every_legacy_path_has_a_destination(self) -> None:
        for legacy, destination in URL_MAP.items():
            with self.subTest(legacy=legacy):
                self.assertTrue(legacy.startswith("/"))
                self.assertTrue(destination.startswith("/"))

    def test_the_crew_pages_are_all_accounted_for(self) -> None:
        for legacy in ("/kidsreccrews", "/adultreccrews", "/competitivecrews"):
            self.assertIn(legacy, URL_MAP)
