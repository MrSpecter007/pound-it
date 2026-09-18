"""
The public page tree.

The home page is a compositor: it owns editorial copy — headings, hero text,
section intros, CTA labels — and sources everything factual from the structured
objects built in earlier phases. No price, schedule or instructor name is
retyped here, so editing a program updates every place it appears.

Index pages do their filtering in ``get_context`` and hand templates finished
lists, keeping query logic out of the markup Codex owns.
"""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path as route_path
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from poundit.blocks import CONTENT_BLOCKS


class PounditHomePage(Page):
    hero_eyebrow = models.CharField(
        max_length=255,
        blank=True,
        help_text='Small line above the headline, e.g. "2026-27 season starts September 14".',
    )
    hero_title = models.CharField(max_length=255, blank=True)
    hero_text = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_video_url = models.URLField(
        blank=True,
        help_text="Optional background or feature video.",
    )

    primary_cta_label = models.CharField(max_length=100, blank=True)
    primary_cta_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Leave empty to fall back to the studio-wide registration URL.",
    )

    intro_copy = models.TextField(blank=True)

    programs_section_title = models.CharField(max_length=255, blank=True, default="Programs")
    programs_section_text = models.TextField(blank=True)
    faculty_section_title = models.CharField(max_length=255, blank=True, default="Faculty")
    faculty_section_text = models.TextField(blank=True)
    events_section_title = models.CharField(max_length=255, blank=True, default="What's on")
    events_section_text = models.TextField(blank=True)

    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField("hero_title"),
        index.SearchField("intro_copy"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_eyebrow"),
                FieldPanel("hero_title"),
                FieldPanel("hero_text"),
                FieldPanel("hero_image"),
                FieldPanel("hero_video_url"),
                FieldPanel("primary_cta_label"),
                FieldPanel("primary_cta_url"),
            ],
            heading="Hero",
        ),
        FieldPanel("intro_copy"),
        MultiFieldPanel(
            [
                FieldPanel("programs_section_title"),
                FieldPanel("programs_section_text"),
                FieldPanel("faculty_section_title"),
                FieldPanel("faculty_section_text"),
                FieldPanel("events_section_title"),
                FieldPanel("events_section_text"),
            ],
            heading="Section copy",
        ),
        FieldPanel("body"),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "poundit.ProgramIndexPage",
        "poundit.SchedulePage",
        "poundit.FacultyIndexPage",
        "poundit.EventIndexPage",
        "poundit.ImportantDatesPage",
        "poundit.SchoolProgramsPage",
        "poundit.ContentPage",
    ]
    template = "poundit/home_page.html"

    class Meta:
        verbose_name = "Pound It home page"

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import (
            CalendarEntry,
            EventPage,
            FacultyMember,
            Program,
            Season,
            TrainingLevel,
        )

        context = super().get_context(request, *args, **kwargs)

        # Featuring is an editorial override, not a precondition. With nothing
        # flagged the home page still fills itself from what exists, so it is
        # never blank just because no one has ticked a box.
        programs = Program.objects.featured()
        if not programs.exists():
            programs = Program.objects.public()

        faculty = FacultyMember.objects.featured()
        if not faculty.exists():
            faculty = FacultyMember.objects.regular()

        context.update(
            {
                "featured_programs": programs[:6],
                "featured_faculty": faculty[:6],
                "upcoming_events": EventPage.objects.upcoming()[:4],
                "upcoming_dates": CalendarEntry.objects.for_season(Season.current())
                .upcoming()
                .order_by("start_date")[:6],
                "training_levels": TrainingLevel.objects.filter(show_in_legend=True),
                "season": Season.current(),
            }
        )
        return context


class ProgramIndexPage(RoutablePageMixin, Page):
    """
    Programs grouped by category.

    Each category is a real URL - /programs/kids-teen/ - so the legacy Wix paths
    redirect to a clean path rather than a query string, which is worth more in
    search. Categories are data, so the route resolves against the database
    instead of a hardcoded list.
    """

    introduction = models.TextField(blank=True)
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = []
    template = "poundit/program_index_page.html"

    class Meta:
        verbose_name = "Programs index"

    @route_path("")
    def all_programs(self, request):
        return self.render(request)

    @route_path("<slug:category_slug>/")
    def by_category(self, request, category_slug: str):
        from django.http import Http404

        from poundit.models import ProgramCategory

        if not ProgramCategory.objects.filter(slug=category_slug).exists():
            raise Http404
        return self.render(request, context_overrides=self._category_context(category_slug))

    def _category_context(self, category_slug: str) -> dict:
        from poundit.models import Program, ProgramCategory

        categories = ProgramCategory.objects.filter(slug=category_slug)
        return {
            "categories": categories,
            "programs_by_category": [
                (category, Program.objects.for_category(category)) for category in categories
            ],
            "active_category": category_slug,
        }

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import Program, ProgramCategory

        context = super().get_context(request, *args, **kwargs)
        categories = ProgramCategory.objects.all()
        # The query parameter still works so old links keep resolving.
        active = request.GET.get("category") if request else None

        if active:
            categories = categories.filter(slug=active)

        context.update(
            {
                "categories": categories,
                "all_categories": ProgramCategory.objects.all(),
                "programs_by_category": [
                    (category, Program.objects.for_category(category))
                    for category in categories
                ],
                "featured_programs": Program.objects.featured(),
                "active_category": active or "",
            }
        )
        return context


class SchedulePage(Page):
    """The weekly grid, rendered from schedule entries rather than an image."""

    introduction = models.TextField(blank=True)
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)
    show_legend = models.BooleanField(default=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("show_legend"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = []
    template = "poundit/schedule_page.html"

    class Meta:
        verbose_name = "Schedule page"

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import (
            ProgramScheduleEntry,
            Season,
            StudioRoom,
            TrainingLevel,
            Weekday,
        )

        context = super().get_context(request, *args, **kwargs)
        season = Season.current()
        entries = ProgramScheduleEntry.objects.for_season(season).public()
        grid = entries.grid()

        rooms = list(StudioRoom.objects.filter(is_active=True))

        # Django templates cannot index a dict by a variable key, so the week is
        # also handed over as a finished nested list. ``grid`` stays available
        # for anything working in Python.
        schedule = [
            {
                "weekday": value,
                "label": Weekday(value).label,
                "rooms": [
                    {"room": room, "entries": grid[value].get(room.id, [])}
                    for room in rooms
                ],
            }
            for value in sorted(grid.keys())
        ]

        from poundit.schedule import build_timelines

        context.update(
            {
                "grid": grid,
                "schedule": schedule,
                "timelines": build_timelines(schedule),
                "rooms": rooms,
                "levels": TrainingLevel.objects.filter(show_in_legend=True),
                "season": season,
            }
        )
        return context


class FacultyIndexPage(Page):
    introduction = models.TextField(blank=True)
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = []
    template = "poundit/faculty_index_page.html"

    class Meta:
        verbose_name = "Faculty index"

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import FacultyMember

        context = super().get_context(request, *args, **kwargs)
        context.update(
            {
                "faculty": FacultyMember.objects.regular(),
                "occasional_faculty": FacultyMember.objects.occasional(),
            }
        )
        return context


class ImportantDatesPage(Page):
    """Generated from calendar entries, not maintained as a list in a rich text field."""

    introduction = models.TextField(blank=True)
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)
    show_past_dates = models.BooleanField(
        default=True,
        help_text="Uncheck to show only dates still to come.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("show_past_dates"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = []
    template = "poundit/important_dates_page.html"

    class Meta:
        verbose_name = "Important dates page"

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import CalendarCategory, CalendarEntry, Season

        context = super().get_context(request, *args, **kwargs)
        season = Season.current()
        entries = CalendarEntry.objects.for_season(season)

        if not self.show_past_dates:
            entries = entries.upcoming()

        active = request.GET.get("category") if request else None
        if active:
            entries = entries.of_category(active)

        context.update(
            {
                "entries_by_month": entries.by_month(),
                "categories": CalendarCategory.objects.all(),
                "active_category": active or "",
                "season": season,
                "has_tentative": entries.filter(is_tentative=True).exists(),
            }
        )
        return context


class ContentPage(Page):
    """
    General editorial page: About, Contact, legal copy.

    One flexible model rather than a page type per section, matching how the
    project already uses a single generic page for everything incidental.
    """

    introduction = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("hero_image"),
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage", "poundit.ContentPage"]
    subpage_types = ["poundit.ContentPage"]
    template = "poundit/content_page.html"

    class Meta:
        verbose_name = "Content page"


class SchoolProgramsPage(Page):
    """
    School residencies, with exactly one inquiry flow.

    The source site renders the same contact form twice on this page. Here the
    form lives once and posts back to this URL, redirecting after a successful
    submission so a refresh cannot send it twice.
    """

    introduction = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    grade_range = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "Kindergarten to Grade 9".',
    )
    duration_label = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "Four days, with a performance for the school community".',
    )

    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    show_inquiry_form = models.BooleanField(default=True)
    inquiry_heading = models.CharField(
        max_length=255, blank=True, default="Contact us to book your school"
    )
    inquiry_intro = models.TextField(blank=True)
    inquiry_button_label = models.CharField(max_length=100, blank=True, default="Send inquiry")
    inquiry_success_message = models.TextField(
        blank=True,
        default="Thanks - we have your inquiry and will be in touch shortly.",
    )

    search_fields = Page.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_image"),
                FieldPanel("introduction"),
                FieldPanel("grade_range"),
                FieldPanel("duration_label"),
            ],
            heading="Basic",
        ),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("show_inquiry_form"),
                FieldPanel("inquiry_heading"),
                FieldPanel("inquiry_intro"),
                FieldPanel("inquiry_button_label"),
                FieldPanel("inquiry_success_message"),
            ],
            heading="Inquiry form",
        ),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = []
    template = "poundit/school_programs_page.html"

    class Meta:
        verbose_name = "School programs page"

    def serve(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        from django.template.response import TemplateResponse

        from poundit.forms import SchoolInquiryForm
        from poundit.models import PounditSettings, send_inquiry_notifications

        if request.method == "POST" and self.show_inquiry_form:
            form = SchoolInquiryForm(request.POST)
            if form.is_valid():
                inquiry = form.save()
                studio_settings = PounditSettings.for_request(request)
                send_inquiry_notifications(inquiry, studio_settings)
                # Redirect after POST so a refresh cannot resubmit.
                return redirect(f"{self.url}?submitted=1")
        else:
            form = SchoolInquiryForm()

        context = self.get_context(request, *args, **kwargs)
        context["form"] = form
        context["submitted"] = request.GET.get("submitted") == "1"

        return TemplateResponse(
            request, self.get_template(request, *args, **kwargs), context
        )
