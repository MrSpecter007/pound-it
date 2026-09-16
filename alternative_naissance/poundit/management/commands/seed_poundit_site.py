"""
Build the Pound It page tree and populate site settings.

Creates the home page and its sections, fills in the studio's contact details
and external links, and - unless told otherwise - makes Pound It the default
site so it answers on localhost. Alternative Naissance keeps its own tree and
is moved to its own hostname rather than being touched or removed.

    python manage.py seed_poundit_site --dry-run
    python manage.py seed_poundit_site
    python manage.py seed_poundit_site --no-default-site

Re-runnable: existing pages are found by slug and left alone.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page, Site

from poundit.models import (
    ContentPage,
    EventIndexPage,
    FacultyIndexPage,
    ImportantDatesPage,
    PounditHomePage,
    PounditSettings,
    ProgramIndexPage,
    SchedulePage,
    SchoolProgramsPage,
    Season,
)

AN_HOSTNAME = "alternative-naissance.localhost"
POUNDIT_HOSTNAME = "poundit.localhost"

HOME = {
    "title": "Pound It Hip Hop Studios",
    "slug": "poundit",
    "hero_eyebrow": "2026-27 season starts September 14",
    "hero_title": "Central Alberta's home of hip hop",
    "hero_text": (
        "Hip Hop, Breaking, Locking, Waacking, House, Litefeet, choreography and other "
        "street and club dance styles, for children, youth and adults."
    ),
    "primary_cta_label": "Register",
    "programs_section_title": "Programs",
    "faculty_section_title": "Faculty",
    "events_section_title": "What's on",
}

# (model, title, slug)
SECTIONS = [
    (ProgramIndexPage, "Programs", "programs"),
    (SchedulePage, "Schedule", "schedule"),
    (FacultyIndexPage, "Faculty", "faculty"),
    (EventIndexPage, "Events", "events"),
    (ImportantDatesPage, "Important Dates", "important-dates"),
    (SchoolProgramsPage, "School Programs", "school-programs"),
    (ContentPage, "About", "about"),
    (ContentPage, "Contact", "contact"),
]

LEGAL_CHILDREN = [
    ("Waiver", "waiver"),
    ("Privacy Policy", "privacy"),
    ("Refund Policy", "refund-policy"),
    ("Terms & Conditions", "terms"),
]

SETTINGS_VALUES = {
    "studio_name": "Pound It Hip Hop Studios",
    "tagline": "Central Alberta's home of hip hop",
    "address": "5809 51 Ave #4b\nRed Deer, AB T4N 4H8",
    "phone_number": "(403) 896-7935",
    "opening_hours": "Mon - Thurs 4:00 pm - 9:00 pm",
    "registration_url": "https://app.gostudiopro.com/online/pounditreddeer",
    "registration_cta_label": "Register",
    "dancer_portal_url": "https://app.gostudiopro.com/online/pounditreddeer",
    "instagram_url": "https://www.instagram.com/poundithiphopstudios/",
    "facebook_url": "https://www.facebook.com/PoundItHipHopStudio",
    "tiktok_url": "https://www.tiktok.com/@poundithiphopstudio",
    "youtube_url": "https://www.youtube.com/@poundithiphopstudios3654",
}

REVIEW_NOTES = [
    "The waiver page is an empty shell. Phase 1 keeps the existing external waiver workflow - "
    "put the link in Pound It settings (Waiver URL) rather than rebuilding signature capture.",
    "Privacy, Refund and Terms pages are empty. Paste the existing legal wording in verbatim; "
    "do not let it be rewritten as part of content cleanup.",
    "The School Programs page has facts only - grades and format. Its descriptive copy is "
    "left empty so the studio's own wording can be pasted in verbatim.",
    "The school inquiry form emails the address in Pound It settings (Public email), falling "
    "back to ADMIN_EMAIL. Neither is set, so notifications will only be logged until one is.",
    "The public email address is not published on the source site, so it is left empty.",
    "Maps URL is empty. Add the studio's map listing link in Pound It settings.",
    "No logo is attached. Image import is Phase 7.",
    "Category filtering on Programs and Events uses a query parameter for now; real subpaths "
    "arrive in Phase 8 with the redirect work.",
]


class Command(BaseCommand):
    help = "Build the Pound It page tree, populate settings, and make it the default site."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--no-default-site",
            action="store_true",
            help="Build the tree but leave the existing default site alone.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        make_default: bool = not options["no_default_site"]
        verbose: bool = options.get("verbosity", 1) >= 1

        created: list[str] = []
        existing: list[str] = []

        with transaction.atomic():
            root = Page.objects.filter(depth=1).first()
            if root is None:
                if verbose:
                    self.stderr.write(self.style.ERROR("No page tree root found."))
                return

            home = PounditHomePage.objects.filter(slug=HOME["slug"]).first()
            if home is None:
                created.append(f"home page /{HOME['slug']}")
                home = PounditHomePage(**HOME)
                root.add_child(instance=home)
                home.save_revision().publish()
            else:
                existing.append(f"home page /{HOME['slug']}")

            for model, title, slug in SECTIONS:
                if model.objects.filter(slug=slug).exists():
                    existing.append(f"{title} /{slug}")
                    continue
                created.append(f"{title} /{slug}")
                page = model(title=title, slug=slug)
                if model is SchoolProgramsPage:
                    page.grade_range = "Kindergarten to Grade 9"
                    page.duration_label = (
                        "Four days, with a performance for the school community"
                    )
                home.add_child(instance=page)
                page.save_revision().publish()

            legal = ContentPage.objects.filter(slug="legal").first()
            if legal is None:
                created.append("Legal /legal")
                legal = ContentPage(title="Legal", slug="legal")
                home.add_child(instance=legal)
                legal.save_revision().publish()
            else:
                existing.append("Legal /legal")

            for title, slug in LEGAL_CHILDREN:
                if ContentPage.objects.filter(slug=slug).exists():
                    existing.append(f"{title} /legal/{slug}")
                    continue
                created.append(f"{title} /legal/{slug}")
                page = ContentPage(title=title, slug=slug)
                legal.add_child(instance=page)
                page.save_revision().publish()

            site_note = self._configure_site(home, make_default, verbose)

            if dry_run:
                transaction.set_rollback(True)

        if not verbose:
            return

        for item in created:
            self.stdout.write(self.style.SUCCESS(f"  + {item}"))
        for item in existing:
            self.stdout.write(f"    {item} (already present)")

        summary = f"{len(created)} pages created, {len(existing)} already present"
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"Dry run - nothing written. Would be: {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Pound It site built: {summary}"))
        if site_note:
            self.stdout.write(self.style.WARNING(site_note))

        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Needs a human decision:"))
        for note in REVIEW_NOTES:
            self.stdout.write(f"  - {note}")

    def _configure_site(self, home: PounditHomePage, make_default: bool, verbose: bool) -> str:
        """Point a Site at the Pound It home page and fill in its settings."""
        note = ""

        if make_default:
            previous = (
                Site.objects.filter(is_default_site=True).exclude(root_page=home).first()
            )
            if previous is not None:
                previous.is_default_site = False
                if previous.hostname in ("localhost", "example.com"):
                    previous.hostname = AN_HOSTNAME
                previous.save()
                note = (
                    f"'{previous.site_name or previous.root_page.title}' is no longer the default "
                    f"site and now answers on {previous.hostname}:{previous.port}. Add it to your "
                    f"hosts file to reach it."
                )

        site = Site.objects.filter(root_page=home).first()
        if site is None:
            # (hostname, port) is unique. When we are not taking over as the
            # default site, the existing site still holds localhost, so claim a
            # distinct hostname instead of colliding with it.
            hostname = "localhost" if make_default else POUNDIT_HOSTNAME
            if (
                Site.objects.filter(hostname=hostname, port=80)
                .exclude(root_page=home)
                .exists()
            ):
                hostname = POUNDIT_HOSTNAME

            site = Site.objects.create(
                hostname=hostname,
                port=80,
                root_page=home,
                site_name="Pound It Hip Hop Studios",
                is_default_site=make_default,
            )
            if not make_default:
                note = (
                    f"Pound It is not the default site. It answers on "
                    f"{hostname}:{site.port} - add that to your hosts file, or re-run "
                    f"without --no-default-site to serve it on localhost."
                )
        elif make_default and not site.is_default_site:
            site.is_default_site = True
            site.hostname = "localhost"
            site.save()

        settings_obj = PounditSettings.for_site(site)
        for field, value in SETTINGS_VALUES.items():
            if not getattr(settings_obj, field, ""):
                setattr(settings_obj, field, value)
        if settings_obj.current_season is None:
            settings_obj.current_season = Season.current()
        settings_obj.save()

        return note
