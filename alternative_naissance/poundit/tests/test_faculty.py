"""
Tests for faculty and the instructor relation on the weekly schedule.

Covers:
- name display, including the short form the printed grid uses
- the regular/occasional/featured querysets
- instructors attached per session rather than per program
- programs_taught spanning both relations
- seed counts, idempotency, and the specific decisions taken about this roster
"""

import datetime
from typing import override

from django.core.management import call_command
from django.test import TestCase

from poundit.models import (
    DanceStyle,
    FacultyMember,
    Program,
    ProgramScheduleEntry,
    Season,
    StudioRoom,
    Weekday,
)


class FacultyDisplayTests(TestCase):
    """Three different names, three different jobs."""

    def test_display_name_includes_the_dance_name(self) -> None:
        member = FacultyMember.objects.create(
            name="Dany Antoine", dance_name="Dizzylock", slug="dizzylock"
        )
        self.assertEqual(member.display_name, "Dany Antoine (Dizzylock)")

    def test_display_name_is_just_the_name_without_one(self) -> None:
        member = FacultyMember.objects.create(name="Rico", slug="rico")
        self.assertEqual(member.display_name, "Rico")

    def test_grid_name_prefers_the_explicit_short_name(self) -> None:
        member = FacultyMember.objects.create(
            name="Nathan", dance_name="Deetz", short_name="Nathan", slug="nathan"
        )
        self.assertEqual(member.grid_name, "Nathan")

    def test_grid_name_falls_back_to_the_dance_name(self) -> None:
        member = FacultyMember.objects.create(
            name="Dany Antoine", dance_name="Dizzylock", slug="dizzylock"
        )
        self.assertEqual(member.grid_name, "Dizzylock")

    def test_grid_name_falls_back_to_the_first_name(self) -> None:
        member = FacultyMember.objects.create(name="Allen Collado", slug="allen")
        self.assertEqual(member.grid_name, "Allen")

    def test_biography_prefers_the_full_bio(self) -> None:
        member = FacultyMember.objects.create(
            name="Rico", slug="rico", short_bio="Short", full_bio="<p>Full</p>"
        )
        self.assertEqual(member.biography, "<p>Full</p>")

    def test_biography_falls_back_to_the_short_bio(self) -> None:
        member = FacultyMember.objects.create(name="Rico", slug="rico", short_bio="Short")
        self.assertEqual(member.biography, "Short")


class FacultyQuerySetTests(TestCase):
    @override
    def setUp(self) -> None:
        self.regular = FacultyMember.objects.create(name="Rico", slug="rico", featured=True)
        self.occasional = FacultyMember.objects.create(
            name="Genie", slug="genie", is_occasional=True
        )
        self.retired = FacultyMember.objects.create(name="Gone", slug="gone", active=False)

    def test_regular_excludes_occasional_instructors(self) -> None:
        self.assertEqual(list(FacultyMember.objects.regular()), [self.regular])

    def test_occasional_returns_only_occasional_instructors(self) -> None:
        self.assertEqual(list(FacultyMember.objects.occasional()), [self.occasional])

    def test_inactive_members_are_excluded_everywhere(self) -> None:
        self.assertNotIn(self.retired, FacultyMember.objects.active())
        self.assertNotIn(self.retired, FacultyMember.objects.regular())

    def test_featured_is_a_subset_of_active(self) -> None:
        self.assertEqual(list(FacultyMember.objects.featured()), [self.regular])


class SessionInstructorTests(TestCase):
    """The point of Phase 3: who teaches is a property of the session, not the program."""

    @override
    def setUp(self) -> None:
        self.room = StudioRoom.objects.create(name="Notorious BIG", slug="notorious-big")
        self.rico = FacultyMember.objects.create(
            name="Rico", short_name="Rico", slug="rico", sort_order=10
        )
        self.masha = FacultyMember.objects.create(
            name="Masha", short_name="Masha", slug="masha", sort_order=50
        )
        self.program = Program.objects.create(title="Supergirlz", slug="super-girlz")

    def _entry(self, weekday: int, start: str) -> ProgramScheduleEntry:
        hour, minute = start.split(":")
        return ProgramScheduleEntry.objects.create(
            program=self.program,
            weekday=weekday,
            start_time=datetime.time(int(hour), int(minute)),
            end_time=datetime.time(int(hour) + 1, int(minute)),
            room=self.room,
        )

    def test_instructors_persist_on_a_saved_entry(self) -> None:
        entry = self._entry(Weekday.THURSDAY, "17:15")
        entry.instructors.set([self.rico, self.masha])
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.instructors.count(), 2)

    def test_instructor_display_matches_the_printed_format(self) -> None:
        entry = self._entry(Weekday.THURSDAY, "17:15")
        entry.instructors.set([self.rico, self.masha])
        entry.save()

        self.assertEqual(entry.instructor_display, "Rico / Masha")

    def test_instructor_display_order_follows_faculty_sort_order(self) -> None:
        entry = self._entry(Weekday.THURSDAY, "17:15")
        entry.instructors.set([self.masha, self.rico])
        entry.save()

        # Added Masha first, but Rico sorts ahead of her on the faculty list.
        self.assertEqual(entry.instructor_display, "Rico / Masha")

    def test_instructor_display_is_empty_with_nobody_assigned(self) -> None:
        self.assertEqual(self._entry(Weekday.FRIDAY, "17:15").instructor_display, "")

    def test_the_same_program_can_have_different_instructors_by_day(self) -> None:
        monday = self._entry(Weekday.MONDAY, "19:00")
        monday.instructors.set([self.masha])
        monday.save()
        wednesday = self._entry(Weekday.WEDNESDAY, "17:15")
        wednesday.instructors.set([self.rico])
        wednesday.save()

        self.assertEqual(monday.instructor_display, "Masha")
        self.assertEqual(wednesday.instructor_display, "Rico")

    def test_programs_taught_spans_both_relations(self) -> None:
        entry = self._entry(Weekday.THURSDAY, "17:15")
        entry.instructors.set([self.masha])
        entry.save()
        self.program.faculty.set([self.rico])
        self.program.save()

        self.assertIn(self.program, self.rico.programs_taught)
        self.assertIn(self.program, self.masha.programs_taught)

    def test_programs_taught_does_not_double_count(self) -> None:
        entry = self._entry(Weekday.THURSDAY, "17:15")
        entry.instructors.set([self.rico])
        entry.save()
        self.program.faculty.set([self.rico])
        self.program.save()

        self.assertEqual(self.rico.programs_taught.count(), 1)


class FacultySeedCommandTests(TestCase):
    """The roster, and the specific judgement calls made about it."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)

    def test_seeds_the_whole_roster(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        self.assertEqual(FacultyMember.objects.count(), 9)

    def test_breton_and_genie_are_occasional(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)

        self.assertEqual(
            sorted(m.name for m in FacultyMember.objects.occasional()),
            ["Breton", "Genie"],
        )
        self.assertEqual(
            FacultyMember.objects.get(slug="genie").availability_note,
            "Roughly 1-2 sessions per month.",
        )

    def test_links_instructors_to_sessions(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)

        linked = ProgramScheduleEntry.objects.exclude(instructors=None).distinct().count()
        self.assertEqual(linked, 34)

    def test_co_taught_session_keeps_every_instructor(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        entry = ProgramScheduleEntry.objects.get(
            program__slug="boss-mega-crew-adv", weekday=Weekday.THURSDAY
        )
        self.assertEqual(entry.instructor_display, "Rico / Dizzylock / Breton / Genie")

    def test_departed_faculty_is_not_reseeded(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        self.assertFalse(FacultyMember.objects.filter(slug="masha").exists())

    def test_supergirlz_is_led_by_rico_alone(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        supergirlz = Program.objects.get(slug="super-girlz")

        self.assertEqual([f.name for f in supergirlz.faculty.all()], ["Rico"])
        self.assertEqual(
            supergirlz.schedule_entries.first().instructor_display, "Rico"
        )

    def test_sessions_left_without_an_instructor_are_visibly_empty(self) -> None:
        """These two still run; the person who taught them was removed."""
        call_command("seed_poundit_faculty", verbosity=0)

        for slug in ("piba", "open-house"):
            entry = ProgramScheduleEntry.objects.get(
                program__slug=slug,
                weekday=Weekday.THURSDAY,
                start_time=datetime.time(17, 15) if slug == "piba" else datetime.time(18, 0),
            )
            self.assertEqual(entry.instructors.count(), 0)
            self.assertEqual(entry.instructor_display, "")

    def test_breakers_has_a_different_lead_per_day(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        breakers = Program.objects.get(slug="red-deer-city-breakers")

        self.assertEqual(
            sorted(f.slug for f in breakers.faculty.all()), ["dizzylock", "rico"]
        )

    def test_non_offerings_have_no_instructor(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        rentals = Program.objects.get(slug="studio-rentals")

        for entry in rentals.schedule_entries.all():
            self.assertEqual(entry.instructors.count(), 0)

    def test_biographies_are_left_for_a_human_to_paste(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        self.assertEqual(FacultyMember.objects.exclude(full_bio="").count(), 0)
        self.assertEqual(FacultyMember.objects.exclude(short_bio="").count(), 7)

    def test_styles_are_relations_not_strings(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        rico = FacultyMember.objects.get(slug="rico")

        self.assertEqual(rico.styles.count(), 5)
        self.assertIn(DanceStyle.objects.get(slug="breaking"), rico.styles.all())

    def test_rerunning_creates_no_duplicates(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        call_command("seed_poundit_faculty", verbosity=0)

        self.assertEqual(FacultyMember.objects.count(), 9)
        self.assertEqual(
            ProgramScheduleEntry.objects.get(
                program__slug="super-girlz", weekday=Weekday.THURSDAY
            ).instructors.count(),
            1,
        )

    def test_rerunning_preserves_admin_edits_by_default(self) -> None:
        call_command("seed_poundit_faculty", verbosity=0)
        rico = FacultyMember.objects.get(slug="rico")
        rico.full_bio = "<p>Pasted verbatim from the source site.</p>"
        rico.save()

        call_command("seed_poundit_faculty", verbosity=0)

        rico.refresh_from_db()
        self.assertEqual(rico.full_bio, "<p>Pasted verbatim from the source site.</p>")

    def test_dry_run_writes_nothing(self) -> None:
        call_command("seed_poundit_faculty", "--dry-run", verbosity=0)
        self.assertEqual(FacultyMember.objects.count(), 0)
