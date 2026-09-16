"""
Seed faculty and attach instructors to the weekly schedule.

Names, roles and styles come from the faculty page on pounditdj.com. Who teaches
which session comes from the 2026/2027 schedule graphic, which is the only place
that information exists.

Biographies are deliberately NOT seeded. The source bios are long-form editorial
in the studio's own voice, and paraphrasing them would quietly rewrite the
studio's words. Each member gets a factual one-line ``short_bio`` so listings
render, and ``full_bio`` is left empty to be pasted in verbatim.

    python manage.py seed_poundit_faculty --dry-run
    python manage.py seed_poundit_faculty
"""

from datetime import time
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from poundit.models import (
    DanceStyle,
    FacultyMember,
    Program,
    ProgramScheduleEntry,
    Weekday,
)

MON, TUE, WED, THU, FRI = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
)


def t(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


FACULTY: list[dict[str, Any]] = [
    {
        "slug": "rico", "short_name": "Rico", "name": "Rico", "role": "Studio Owner", "sort_order": 10,
        "short_bio": "Studio owner, from Mexico City. Toured internationally as a lead dancer before founding Pound It.",
        "styles": ["hip-hop", "breaking", "litefeet", "house", "locking"],
    },
    {
        "slug": "cody", "short_name": "Cody", "name": "Cody", "role": "Dance Instructor", "sort_order": 20,
        "short_bio": "Joined Pound It in 2015 as a recreational dancer and now teaches rec and competitive classes.",
        "styles": ["hip-hop", "waacking", "jersey-club", "locking", "animation", "litefeet", "house", "breaking"],
    },
    {
        "slug": "leiran", "short_name": "Leiran", "name": "Leiran", "role": "Dance Instructor", "sort_order": 30,
        "short_bio": "Trained in Okotoks and High River, with provincial and national competitive titles.",
        "styles": ["hip-hop", "waacking", "house", "locking", "litefeet", "afro", "vogue"],
    },
    {
        "slug": "nathan", "short_name": "Nathan", "name": "Nathan", "dance_name": "Deetz",
        "role": "School Residencies and Rec Programs Instructor", "sort_order": 40,
        "short_bio": "Joined Pound It in 2024 and teaches school residencies and rec programs.",
        "styles": ["hip-hop"],
    },
    {
        "slug": "dizzylock", "short_name": "Dizzylock", "name": "Dany Antoine", "dance_name": "Dizzylock",
        "role": "Instructor", "sort_order": 60,
        "short_bio": "Montreal-based street dance artist, educator, battle champion and judge.",
        "styles": ["campbellocking", "hip-hop", "waacking", "popping", "breaking", "house", "locking"],
    },
    {
        "slug": "allen", "short_name": "Allen", "name": "Allen Collado", "role": "Instructor", "sort_order": 70,
        "short_bio": "Co-owner and co-director of The Masses in Calgary, with nine years teaching experience.",
        "styles": ["hip-hop", "atlanta-styles", "house", "choreography"],
    },
    {
        "slug": "charlee", "short_name": "Charlee", "name": "Charlee Martinez", "dance_name": "Difficult C",
        "role": "Youth Programs and Hip Hop Instructor", "sort_order": 80,
        "short_bio": "Battle competitor and emerging educator, trained three summers in New York City.",
        "styles": ["hip-hop", "waacking"],
    },
    {
        "slug": "breton", "short_name": "Breton", "name": "Breton", "role": "Occasional Instructor", "sort_order": 90,
        "is_occasional": True, "availability_note": "Roughly 1-2 sessions per month.",
        "styles": [],
    },
    {
        "slug": "genie", "short_name": "Genie", "name": "Genie", "role": "Occasional Instructor", "sort_order": 100,
        "is_occasional": True, "availability_note": "Roughly 1-2 sessions per month.",
        "styles": [],
    },
]

# (program slug, weekday, start time, [faculty slugs]) straight off the schedule graphic.
ASSIGNMENTS: list[tuple[str, int, str, list[str]]] = [
    # Monday
    ("lil-cuz", MON, "17:15", ["rico"]),
    ("breaking-6-9", MON, "18:00", ["dizzylock"]),
    ("red-deer-city-breakers", MON, "19:00", ["dizzylock"]),
    ("open-locking", MON, "20:00", ["dizzylock"]),
    ("open-waacking", MON, "20:45", ["dizzylock"]),
    ("the-broskies", MON, "17:00", ["nathan"]),
    ("la-familia-jr", MON, "18:00", ["rico"]),
    ("lite-feet-10-15", MON, "19:00", ["rico"]),
    # Tuesday
    ("la-bandita", TUE, "17:15", ["rico"]),
    ("la-familia", TUE, "18:00", ["dizzylock"]),
    ("piba", TUE, "19:00", ["rico"]),
    ("open-hip-hop", TUE, "19:45", ["dizzylock"]),
    ("ak42s", TUE, "20:30", ["rico"]),
    ("bambinos", TUE, "16:30", ["rico"]),
    ("chicken-noodle-soup", TUE, "17:00", ["charlee"]),
    ("hip-hop-6-9", TUE, "17:30", ["nathan"]),
    ("popping-10-15", TUE, "19:00", ["dizzylock"]),
    ("open-breaking", TUE, "20:30", ["dizzylock"]),
    # Wednesday
    ("chicos", WED, "17:15", ["nathan"]),
    ("choreography-class", WED, "18:00", ["allen"]),
    ("open-atlanta-styles", WED, "19:15", ["allen"]),
    ("lulu-100s", WED, "20:15", ["rico"]),
    ("chicken-noodle-soup", WED, "16:30", ["charlee"]),
    ("red-deer-city-breakers", WED, "17:15", ["rico"]),
    ("riverside-bounce", WED, "18:00", ["rico"]),
    ("hip-hop-10-15", WED, "19:00", ["nathan"]),
    ("open-jersey-club", WED, "19:45", ["cody"]),
    ("piba", WED, "20:30", ["cody"]),
    # Thursday
    ("hip-hop-6-9", THU, "16:30", ["nathan"]),
    ("super-girlz", THU, "17:15", ["rico"]),
    ("boss-mega-crew-adv", THU, "18:15", ["rico", "dizzylock", "breton", "genie"]),
    ("battle-training", THU, "19:15", ["rico"]),
    ("revolution", THU, "20:15", ["rico", "dizzylock", "allen"]),
    ("open-styles", THU, "16:30", ["dizzylock"]),
]

REVIEW_NOTES = [
    "Biographies are intentionally empty. Paste the verbatim text from pounditdj.com/faculty "
    "into each member's Full bio rather than letting a summary stand in for the studio's words.",
    "The faculty page lists Dizzylock and Allen Collado as guest or visiting instructors, but the "
    "2026/27 schedule has them teaching weekly. Roles seeded as 'Instructor' - confirm.",
    "Breton and Genie teach on the schedule but have no faculty page entry. Seeded as occasional "
    "instructors at roughly 1-2 sessions per month, with no bio or styles.",
    "Leiran appears on the faculty page but on no session in the 2026/27 schedule.",
    "Leiran's styles include tap, jazz, ballet, lyrical, contemporary, pointe and musical theatre, "
    "which are not in the dance style taxonomy. Only the street and club styles were attached.",
    "Program-level faculty is derived: the lead instructor of each of a program's sessions. The "
    "source site does not publish program leads, so verify before launch.",
    "PIBA Thursday 5:15-6:00 and Open House Thursday 6:00-6:45 have NO instructor assigned. "
    "Both still run on the 2026/27 schedule but the person who taught them has been removed. "
    "Assign a replacement in the admin.",
    "Portraits are not attached. Image import is Phase 7.",
]


class Command(BaseCommand):
    help = "Seed faculty and attach instructors to the weekly schedule. Idempotent."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--update",
            action="store_true",
            help="Overwrite existing faculty with these defaults, discarding admin edits.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        update: bool = options["update"]
        verbose: bool = options.get("verbosity", 1) >= 1

        styles = {style.slug: style for style in DanceStyle.objects.all()}
        created = updated = skipped = 0
        linked = 0
        missing_entries: list[str] = []

        with transaction.atomic():
            for spec in FACULTY:
                slug = spec["slug"]
                existing = FacultyMember.objects.filter(slug=slug).first()
                fields = {
                    "name": spec["name"],
                    "short_name": spec.get("short_name", ""),
                    "dance_name": spec.get("dance_name", ""),
                    "role": spec.get("role", ""),
                    "short_bio": spec.get("short_bio", ""),
                    "is_occasional": spec.get("is_occasional", False),
                    "availability_note": spec.get("availability_note", ""),
                    "sort_order": spec.get("sort_order", 0),
                }

                if existing is None:
                    created += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"  + Faculty: {slug}"))
                    if not dry_run:
                        member = FacultyMember.objects.create(slug=slug, **fields)
                        member.styles.set(
                            [styles[s] for s in spec.get("styles", []) if s in styles]
                        )
                        member.save()
                elif update:
                    updated += 1
                    if verbose:
                        self.stdout.write(self.style.WARNING(f"  ~ Faculty: {slug}"))
                    if not dry_run:
                        for key, value in fields.items():
                            setattr(existing, key, value)
                        existing.styles.set(
                            [styles[s] for s in spec.get("styles", []) if s in styles]
                        )
                        existing.save()
                else:
                    skipped += 1

            if dry_run:
                transaction.set_rollback(True)
                if verbose:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Dry run - nothing written. Would be: {created} faculty created, "
                            f"{len(ASSIGNMENTS)} sessions linked."
                        )
                    )
                self._print_notes(verbose)
                return

            members = {m.slug: m for m in FacultyMember.objects.all()}

            for program_slug, weekday, start, instructor_slugs in ASSIGNMENTS:
                entry = ProgramScheduleEntry.objects.filter(
                    program__slug=program_slug, weekday=weekday, start_time=t(start)
                ).first()
                if entry is None:
                    missing_entries.append(f"{program_slug} {Weekday(weekday).label} {start}")
                    continue
                entry.instructors.set(
                    [members[s] for s in instructor_slugs if s in members]
                )
                entry.save()
                linked += 1

            # Program-level lead faculty: the first instructor of each of its sessions.
            for program in Program.objects.all():
                leads: list = []
                for entry in program.schedule_entries.all().order_by("weekday", "start_time"):
                    first = entry.instructors.first()
                    if first is not None and first not in leads:
                        leads.append(first)
                if leads:
                    program.faculty.set(leads)
                    program.save()

        if verbose:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Faculty seeded: {created} created, {updated} updated, {skipped} left untouched, "
                    f"{linked} sessions linked to instructors"
                )
            )
            if missing_entries:
                self.stdout.write(self.style.ERROR("Schedule entries not found:"))
                for item in missing_entries:
                    self.stdout.write(f"  - {item}")
        self._print_notes(verbose)

    def _print_notes(self, verbose: bool) -> None:
        if not verbose:
            return
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Needs a human decision:"))
        for note in REVIEW_NOTES:
            self.stdout.write(f"  - {note}")
