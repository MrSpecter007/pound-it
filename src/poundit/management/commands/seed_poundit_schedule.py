"""
Seed the 2026/2027 programs and weekly schedule.

Facts come from two sources that do not fully agree:

* the studio's 2026/2027 weekly schedule graphic — authoritative for days,
  times and rooms, because it is the one labelled with this season;
* the rec/competitive crew pages on pounditdj.com — authoritative for tuition,
  audition requirements, categories and descriptions.

Where the two conflict the graphic wins for timing and the crew page wins for
money, and every conflict is printed at the end for a human to settle. Nothing
here silently rewrites a price or a time.

    python manage.py seed_poundit_schedule --dry-run
    python manage.py seed_poundit_schedule
"""

from datetime import time
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from poundit.models import (
    Program,
    ProgramCategory,
    ProgramInclusion,
    ProgramScheduleEntry,
    ProgramTuitionOption,
    Season,
    StudioRoom,
    TrainingLevel,
    Weekday,
)

MON, TUE, WED, THU, FRI = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
)
NB = "notorious-big"
BY = "black-and-yellow"

REGISTRATION_URL = "https://app.gostudiopro.com/online/pounditreddeer"


def t(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


# Each entry: (weekday, start, end, room_slug, label_override)
PROGRAMS: list[dict[str, Any]] = [
    # ---------------- Kids & Teen Rec ----------------
    {
        "slug": "bambinos", "title": "Bambinos", "category": "kids-teen", "level": "age-2-3",
        "age_min": 2, "age_max": 3,
        "tuition_amount": Decimal("125"), "tuition_period": "session",
        "tuition_note": "$125 for 6-week sessions.",
        "short_description": "Introduction to movement, music and dance for toddlers with caregivers.",
        "styles": ["hip-hop"],
        "entries": [(TUE, "16:30", "17:00", BY, "")],
    },
    {
        "slug": "chicken-noodle-soup", "title": "Chicken Noodle Soup Crew", "category": "kids-teen",
        "level": "age-4-5", "age_min": 4, "age_max": 5,
        "tuition_amount": Decimal("105"), "tuition_period": "month",
        "short_description": "Hip hop foundations with a focus on confidence, musicality and teamwork.",
        "inclusions": ["Performances", "Year-end costume"],
        "styles": ["hip-hop"],
        "entries": [(TUE, "17:00", "17:30", BY, ""), (WED, "16:30", "17:00", BY, "Hip Hop")],
    },
    {
        "slug": "lil-cuz", "title": "Lil Cuz Crew", "category": "kids-teen", "level": "crew",
        "age_min": 6, "age_max": 9,
        "tuition_amount": Decimal("135"), "tuition_period": "month",
        "short_description": "Hip hop foundations with optional training in Hip Hop and Breaking.",
        "inclusions": ["2 performances", "Costume"],
        "styles": ["hip-hop", "breaking"],
        "entries": [(MON, "17:15", "18:00", NB, "")],
    },
    {
        "slug": "chicos", "title": "Chicos Crew", "category": "kids-teen", "level": "crew",
        "age_min": 6, "age_max": 9,
        "tuition_amount": Decimal("135"), "tuition_period": "month",
        "short_description": "Hip hop foundations with optional training in Hip Hop and Breaking.",
        "inclusions": ["2 performances", "Costume"],
        "styles": ["hip-hop", "breaking"],
        "entries": [(WED, "17:15", "18:00", NB, "")],
    },
    {
        "slug": "riverside-bounce", "title": "Riverside Bounce Rec Crew", "category": "kids-teen",
        "level": "crew", "age_min": 10, "age_max": 15,
        "tuition_amount": Decimal("135"), "tuition_period": "month",
        "short_description": "Advanced hip hop with optional training in Litefeet, Popping, Hip Hop and Open Styles.",
        "inclusions": ["2 performances", "Costume"],
        "styles": ["hip-hop", "litefeet", "popping"],
        "entries": [(WED, "18:00", "18:45", BY, "")],
    },
    # ---------------- Competitive ----------------
    {
        "slug": "la-bandita", "title": "La Bandita Competitive Crew", "category": "competitive",
        "level": "crew", "age_min": 6, "audition_required": False,
        "tuition_amount": Decimal("230"), "tuition_period": "month",
        "short_description": "Introductory competitive crew focusing on technical foundations, teamwork and confidence.",
        "inclusions": ["Unlimited training classes", "3 spring competitions"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(TUE, "17:15", "18:00", NB, "")],
    },
    {
        "slug": "super-girlz", "title": "Supergirlz Competitive Crew", "category": "competitive",
        "level": "crew", "audition_required": False,
        "tuition_amount": Decimal("270"), "tuition_period": "month",
        "short_description": "Girl-empowerment focused program emphasising fierce, feminine choreography.",
        "inclusions": ["Unlimited classes", "2 exclusive masterclass workshops"],
        "styles": ["hip-hop", "choreography", "waacking"],
        "entries": [(THU, "17:15", "18:15", NB, "")],
    },
    {
        "slug": "red-deer-city-breakers", "title": "Red Deer City Breakers Competitive Crew",
        "category": "competitive", "level": "crew", "audition_required": True,
        "tuition_amount": Decimal("280"), "tuition_period": "month",
        "short_description": "Premier Breaking crew emphasising power, strength, musicality and creativity.",
        "inclusions": ["2 exclusive masterclass workshops"],
        "styles": ["breaking"],
        "entries": [
            (MON, "19:00", "20:00", NB, "Power & Strength Training"),
            (WED, "17:15", "18:00", BY, "Crew Choreography"),
        ],
    },
    {
        "slug": "la-familia-jr", "title": "La Familia Jr. Competitive Crew", "category": "competitive",
        "level": "crew", "audition_required": True,
        "tuition_amount": Decimal("270"), "tuition_period": "month",
        "short_description": "For dancers with strong foundational training, developing refined technique and performance quality.",
        "inclusions": ["2 masterclass workshops"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(MON, "18:00", "19:00", BY, "")],
    },
    {
        "slug": "la-familia", "title": "La Familia Competitive Crew", "category": "competitive",
        "level": "crew", "audition_required": True, "age_label": "Teen",
        "tuition_amount": Decimal("270"), "tuition_period": "month",
        "short_description": "Premier teen advanced crew for passionate dancers.",
        "inclusions": ["Provincial battles", "Community festival performances", "2 masterclass workshops"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(TUE, "18:00", "19:00", NB, "")],
    },
    {
        "slug": "revolution", "title": "Revolution Competitive Crew", "category": "competitive",
        "level": "crew", "audition_required": True, "age_label": "All ages",
        "tuition_amount": Decimal("250"), "tuition_period": "month",
        "short_description": "Highest-level crew emphasising excellence, innovative choreography and outstanding performance.",
        "inclusions": ["2 masterclass workshops"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(THU, "20:15", "21:15", NB, "")],
    },
    {
        "slug": "ak42s", "title": "AK42s Competitive Adult Crew", "category": "competitive",
        "level": "crew", "audition_required": False, "age_min": 18,
        "tuition_amount": Decimal("250"), "tuition_period": "month",
        "short_description": "Adult crew for dancers balancing work and life, focused on performance quality, musicality and teamwork.",
        "inclusions": ["2 masterclass workshops"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(TUE, "20:30", "21:30", NB, "")],
    },
    # ---------------- Adult Rec ----------------
    {
        "slug": "lulu-100s", "title": "LULU 100s Adult Rec Crew", "category": "adult",
        "level": "crew", "age_min": 16,
        "tuition_amount": Decimal("135"), "tuition_period": "month",
        "short_description": "Authentic hip hop choreography in a supportive, judgment-free environment, in partnership with lululemon.",
        "inclusions": ["Unlimited training classes", "2 performances annually"],
        "styles": ["hip-hop", "choreography"],
        "entries": [(WED, "20:15", "21:00", NB, "")],
    },
    {
        "slug": "piba", "title": "PIBA - Pound It Beginner Adults", "category": "adult",
        "level": "piba", "age_min": 18,
        "tuition_note": "No competitions or performances.",
        "short_description": "Hip hop and street dance for all experience levels, focused on fitness, stress relief and meeting new people.",
        "tuition_options": [
            ("1 class per week", Decimal("70"), "month", ""),
            ("2 classes per week", Decimal("95"), "month", ""),
            ("Unlimited training pass", Decimal("115"), "month", ""),
            ("Punch pass", Decimal("175"), "", "10 classes"),
            ("Drop-in", Decimal("25"), "class", ""),
        ],
        "styles": ["hip-hop"],
        "entries": [
            (TUE, "19:00", "19:45", NB, ""),
            (WED, "20:30", "21:15", BY, ""),
            (THU, "17:15", "18:00", BY, ""),
        ],
    },
    # ---------------- Open training / technique ----------------
    {
        "slug": "breaking-6-9", "title": "Breaking (6-9)", "category": "open-training",
        "level": "age-6-9", "age_min": 6, "age_max": 9, "styles": ["breaking"],
        "entries": [(MON, "18:00", "18:45", NB, "")],
    },
    {
        "slug": "lite-feet-10-15", "title": "Lite Feet (10-15)", "category": "open-training",
        "level": "age-10-15", "age_min": 10, "age_max": 15, "styles": ["litefeet"],
        "entries": [(MON, "19:00", "19:45", BY, "")],
    },
    {
        "slug": "hip-hop-6-9", "title": "Hip Hop (6-9)", "category": "open-training",
        "level": "age-6-9", "age_min": 6, "age_max": 9, "styles": ["hip-hop"],
        "entries": [(TUE, "17:30", "18:15", BY, ""), (THU, "16:30", "17:15", NB, "")],
    },
    {
        "slug": "popping-10-15", "title": "Popping (10-15)", "category": "open-training",
        "level": "age-10-15", "age_min": 10, "age_max": 15, "styles": ["popping"],
        "entries": [(TUE, "19:00", "19:45", BY, "")],
    },
    {
        "slug": "hip-hop-10-15", "title": "Hip Hop (10-15)", "category": "open-training",
        "level": "age-10-15", "age_min": 10, "age_max": 15, "styles": ["hip-hop"],
        "entries": [(WED, "19:00", "19:45", BY, "")],
    },
    {
        "slug": "choreography-class", "title": "Choreography", "category": "open-training",
        "level": "choreography", "styles": ["choreography"],
        "entries": [(WED, "18:00", "19:15", NB, "")],
    },
    {
        "slug": "choreography-cleaning", "title": "Choreography Cleaning", "category": "open-training",
        "level": "choreography", "styles": ["choreography"],
        "entries": [(FRI, "17:15", "19:00", NB, "")],
    },
    {
        "slug": "battle-training", "title": "Battle Training", "category": "open-training",
        "level": "crew", "styles": ["hip-hop", "breaking"],
        "entries": [(THU, "19:15", "20:15", NB, "")],
    },
    {
        "slug": "open-locking", "title": "Open Locking", "category": "open-training",
        "level": "open", "styles": ["locking"],
        "entries": [(MON, "20:00", "20:45", NB, "")],
    },
    {
        "slug": "open-waacking", "title": "Open Waacking", "category": "open-training",
        "level": "open", "styles": ["waacking"],
        "entries": [(MON, "20:45", "21:30", NB, "")],
    },
    {
        "slug": "open-hip-hop", "title": "Open Hip Hop", "category": "open-training",
        "level": "open", "styles": ["hip-hop"],
        "entries": [(TUE, "19:45", "20:30", NB, "")],
    },
    {
        "slug": "open-breaking", "title": "Open Breaking", "category": "open-training",
        "level": "open", "styles": ["breaking"],
        "entries": [(TUE, "20:30", "21:15", BY, "")],
    },
    {
        "slug": "open-atlanta-styles", "title": "Open Atlanta Styles", "category": "open-training",
        "level": "open", "styles": ["atlanta-styles"],
        "entries": [(WED, "19:15", "20:00", NB, "")],
    },
    {
        "slug": "open-jersey-club", "title": "Open Jersey Club", "category": "open-training",
        "level": "open", "styles": ["jersey-club"],
        "entries": [(WED, "19:45", "20:30", BY, "")],
    },
    {
        "slug": "open-styles", "title": "Open Styles", "category": "open-training",
        "level": "open", "styles": ["hip-hop"],
        "entries": [(THU, "16:30", "17:15", BY, "")],
    },
    {
        "slug": "open-house", "title": "Open House", "category": "open-training",
        "level": "open", "styles": ["house"],
        "entries": [(THU, "18:00", "18:45", BY, "")],
    },
    # ---------------- Crews with no source page (category pending review) ----------------
    {
        "slug": "the-broskies", "title": "The Broskies", "category": "other", "level": "crew",
        "entries": [(MON, "17:00", "18:00", BY, "")],
    },
    {
        "slug": "boss-mega-crew-adv", "title": "Boss Mega Crew Adv.", "category": "other", "level": "crew",
        "entries": [(THU, "18:15", "19:15", NB, "")],
    },
    # ---------------- Schedule occupancy, not offerings ----------------
    {
        "slug": "private-training", "title": "Private Training", "category": "other",
        "level": "private", "is_public": False,
        "entries": [
            (TUE, "16:30", "17:15", NB, ""),
            (TUE, "19:45", "20:30", BY, ""),
            (THU, "18:45", "21:00", BY, ""),
            (FRI, "17:15", "21:00", BY, ""),
        ],
    },
    {
        "slug": "studio-rentals", "title": "Studio Rentals", "category": "other",
        "level": "private", "is_public": False,
        "entries": [
            (MON, "16:30", "17:15", NB, ""),
            (WED, "16:30", "17:15", NB, ""),
            (FRI, "19:30", "20:30", NB, ""),
        ],
    },
]

REVIEW_NOTES = [
    "Red Deer City Breakers: crew page says Mon 6:45 PM and Wed 5:00 PM; the 2026/27 graphic "
    "says Mon 7:00-8:00 and Wed 5:15-6:00. Seeded from the graphic.",
    "La Familia Jr.: crew page says Mon 7:45 PM; the graphic says Mon 6:00-7:00. Seeded from the graphic.",
    "PIBA Wednesday: crew page says 8:15 PM; the graphic says 8:30-9:15. Seeded from the graphic.",
    "The Wednesday 4:30 'Hip Hop' (ages 4-5, Charlee) is seeded as Chicken Noodle Soup's second "
    "weekly session, per the kids rec crew page. Confirm.",
    "The Broskies has no page on the source site. Category left as 'Other' - needs assigning.",
    "Boss Mega Crew Adv. has no page on the source site. Category left as 'Other' - needs assigning.",
    "The crew page spells it 'Supergirlz'; the schedule graphic reads 'Super Girlz'. Using 'Supergirlz'.",
    "Tuition is not published for any open-training class. Those programs have no price set.",
]


class Command(BaseCommand):
    help = "Seed the 2026/2027 programs and weekly schedule. Idempotent."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--season",
            default=None,
            help="Season slug to attach to. Defaults to the current season.",
        )

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

        categories = {c.slug: c for c in ProgramCategory.objects.all()}
        levels = {level.slug: level for level in TrainingLevel.objects.all()}
        rooms = {room.slug: room for room in StudioRoom.objects.all()}

        programs_created = entries_created = skipped = 0

        with transaction.atomic():
            for order, spec in enumerate(PROGRAMS, start=1):
                slug = spec["slug"]
                existing = Program.objects.filter(slug=slug).first()

                if existing is None:
                    programs_created += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"  + Program: {slug}"))
                    program = Program(
                        slug=slug,
                        title=spec["title"],
                        category=categories.get(spec.get("category")),
                        level=levels.get(spec.get("level")),
                        season=season,
                        short_description=spec.get("short_description", ""),
                        age_min=spec.get("age_min"),
                        age_max=spec.get("age_max"),
                        age_label=spec.get("age_label", ""),
                        audition_required=spec.get("audition_required", False),
                        tuition_amount=spec.get("tuition_amount"),
                        tuition_period=spec.get("tuition_period", ""),
                        tuition_note=spec.get("tuition_note", ""),
                        registration_url="" if not spec.get("is_public", True) else REGISTRATION_URL,
                        is_public=spec.get("is_public", True),
                        sort_order=order * 10,
                    )
                    if not dry_run:
                        program.save()
                        if spec.get("styles"):
                            program.styles.set(
                                [s for s in program.styles.model.objects.filter(slug__in=spec["styles"])]
                            )
                            program.save()
                        for i, text in enumerate(spec.get("inclusions", []), start=1):
                            ProgramInclusion.objects.create(program=program, text=text, sort_order=i)
                        for i, (label, amount, period, note) in enumerate(
                            spec.get("tuition_options", []), start=1
                        ):
                            ProgramTuitionOption.objects.create(
                                program=program, label=label, amount=amount,
                                period=period, note=note, sort_order=i,
                            )
                else:
                    program = existing
                    skipped += 1

                if dry_run:
                    entries_created += len(spec["entries"])
                    continue

                for i, (weekday, start, end, room_slug, label) in enumerate(spec["entries"], start=1):
                    _, made = ProgramScheduleEntry.objects.get_or_create(
                        program=program,
                        weekday=weekday,
                        start_time=t(start),
                        defaults={
                            "end_time": t(end),
                            "room": rooms.get(room_slug),
                            "season": season,
                            "label": label,
                            "sort_order": i,
                        },
                    )
                    if made:
                        entries_created += 1

            if dry_run:
                transaction.set_rollback(True)

        summary = (
            f"{programs_created} programs created, {skipped} already present, "
            f"{entries_created} schedule entries created"
        )
        if not verbose:
            return
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Schedule seeded for {season.label}: {summary}"))

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Needs a human decision:"))
        for note in REVIEW_NOTES:
            self.stdout.write(f"  - {note}")
