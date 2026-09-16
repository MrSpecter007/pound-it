"""
Events: battles, workshops, camps, performances, competitions, festivals, intensives.

Upcoming and past are computed from the data, not maintained by hand. An event
falls out of "upcoming" the moment it actually finishes — which for a multi-day
camp means its end, not its start — so nobody has to remember to pull a finished
event off the homepage.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path as route_path
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.search import index

from poundit.blocks import CONTENT_BLOCKS


class EventStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    SOLD_OUT = "sold_out", "Sold out"
    POSTPONED = "postponed", "Postponed"
    CANCELLED = "cancelled", "Cancelled"


class EventPageQuerySet(PageQuerySet):
    def _visible(self) -> "EventPageQuerySet":
        return self.live().public()

    def upcoming(self) -> "EventPageQuerySet":
        """
        Still to happen, or happening now.

        Keyed on the end of the event where one is set, so a four-day camp stays
        upcoming through its final day instead of vanishing after day one.
        """
        now = timezone.now()
        return (
            self._visible()
            .annotate(
                _finishes_at=models.functions.Coalesce("end_datetime", "start_datetime")
            )
            .filter(_finishes_at__gte=now)
            .exclude(status=EventStatus.CANCELLED)
            .order_by("start_datetime")
        )

    def past(self) -> "EventPageQuerySet":
        now = timezone.now()
        return (
            self._visible()
            .annotate(
                _finishes_at=models.functions.Coalesce("end_datetime", "start_datetime")
            )
            .filter(_finishes_at__lt=now)
            .order_by("-start_datetime")
        )

    def featured(self) -> "EventPageQuerySet":
        return self.upcoming().filter(featured=True)

    def of_type(self, event_type) -> "EventPageQuerySet":
        slug = getattr(event_type, "slug", event_type)
        return self.filter(event_type__slug=slug)


EventPageManager = PageManager.from_queryset(EventPageQuerySet)


class EventPage(Page):
    # ``core`` already has an EventPage. Django derives the multi-table-inheritance
    # reverse accessor from the model name, so both would claim ``Page.eventpage``.
    # Naming the parent link here resolves it without touching core.
    page_ptr = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        parent_link=True,
        primary_key=True,
        related_name="poundit_eventpage",
    )

    event_type = models.ForeignKey(
        "poundit.EventType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="One line, used on event cards and listings.",
    )
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    poster_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="The event flyer, if there is one. Usually portrait.",
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set this for anything spanning more than one day, so it stays listed until it ends.",
    )

    venue_name = models.CharField(max_length=255, blank=True)
    venue_address = models.TextField(blank=True)

    price_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_text = models.CharField(
        max_length=255,
        blank=True,
        help_text='Use when a single figure will not do, e.g. "$20 spectator / $35 competitor".',
    )

    age_label = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    registration_url = models.URLField(blank=True)
    external_url = models.URLField(
        blank=True,
        help_text="An organiser's own page, when Pound It is not the host.",
    )

    related_faculty = ParentalManyToManyField(
        "poundit.FacultyMember", blank=True, related_name="events"
    )
    related_programs = ParentalManyToManyField(
        "poundit.Program", blank=True, related_name="events"
    )
    related_styles = ParentalManyToManyField(
        "poundit.DanceStyle", blank=True, related_name="events"
    )

    status = models.CharField(
        max_length=20, choices=EventStatus.choices, default=EventStatus.SCHEDULED
    )
    featured = models.BooleanField(default=False)

    objects = EventPageManager()

    search_fields = Page.search_fields + [
        index.SearchField("short_description"),
        index.SearchField("body"),
        index.SearchField("venue_name"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("event_type"),
                FieldPanel("short_description"),
                FieldPanel("hero_image"),
                FieldPanel("poster_image"),
            ],
            heading="Basic",
        ),
        MultiFieldPanel(
            [
                FieldPanel("start_datetime"),
                FieldPanel("end_datetime"),
            ],
            heading="When",
        ),
        MultiFieldPanel(
            [
                FieldPanel("venue_name"),
                FieldPanel("venue_address"),
            ],
            heading="Where",
        ),
        MultiFieldPanel(
            [
                FieldPanel("price_amount"),
                FieldPanel("price_text"),
                FieldPanel("age_label"),
                FieldPanel("capacity"),
            ],
            heading="Admission",
        ),
        MultiFieldPanel(
            [
                FieldPanel("registration_url"),
                FieldPanel("external_url"),
            ],
            heading="Registration",
        ),
        MultiFieldPanel(
            [
                FieldPanel("related_faculty"),
                FieldPanel("related_programs"),
                FieldPanel("related_styles"),
            ],
            heading="Relationships",
        ),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("status"),
                FieldPanel("featured"),
            ],
            heading="Publishing",
        ),
    ]

    parent_page_types = ["poundit.EventIndexPage"]
    subpage_types = []
    template = "poundit/event_page.html"

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    @property
    def finishes_at(self):
        return self.end_datetime or self.start_datetime

    @property
    def is_past(self) -> bool:
        return self.finishes_at < timezone.now()

    @property
    def is_multi_day(self) -> bool:
        if self.end_datetime is None:
            return False
        return self.end_datetime.date() > self.start_datetime.date()

    @property
    def price_display(self) -> str:
        if self.price_text:
            return self.price_text
        if self.price_amount is not None:
            amount = (
                self.price_amount.quantize(Decimal("1"))
                if self.price_amount == self.price_amount.to_integral()
                else self.price_amount
            )
            return f"${amount}"
        return ""

    @property
    def date_display(self) -> str:
        """"3 April 2027" or "30 March - 2 April 2027"."""
        start = self.start_datetime
        if not self.is_multi_day:
            return start.strftime("%-d %B %Y")
        end = self.end_datetime
        if start.year != end.year:
            return f"{start.strftime('%-d %B %Y')} - {end.strftime('%-d %B %Y')}"
        if start.month != end.month:
            return f"{start.strftime('%-d %B')} - {end.strftime('%-d %B %Y')}"
        return f"{start.strftime('%-d')} - {end.strftime('%-d %B %Y')}"


class EventIndexPage(RoutablePageMixin, Page):
    """
    Listing page for events.

    Event types get real URLs - /events/workshop/ - but event pages are children
    of this page and live at /events/<slug>/ too. RoutablePageMixin tries its own
    routes before children, so without the guard in ``route`` below an event
    would be shadowed by a type filter that happened to share its slug.
    """

    introduction = models.TextField(blank=True)
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    parent_page_types = ["poundit.PounditHomePage"]
    subpage_types = ["poundit.EventPage"]
    template = "poundit/event_index_page.html"

    class Meta:
        verbose_name = "Events index"

    def route(self, request, path_components):
        """A real event page always wins over a type filter of the same slug."""
        if path_components and self.get_children().filter(slug=path_components[0]).exists():
            return Page.route(self, request, path_components)
        return super().route(request, path_components)

    @route_path("")
    def all_events(self, request):
        return self.render(request)

    @route_path("<slug:type_slug>/")
    def by_type(self, request, type_slug: str):
        from django.http import Http404

        from poundit.models import EventType

        if not EventType.objects.filter(slug=type_slug).exists():
            raise Http404
        return self.render(
            request,
            context_overrides={
                "upcoming": EventPage.objects.child_of(self).upcoming().of_type(type_slug),
                "past": EventPage.objects.child_of(self).past().of_type(type_slug),
                "active_type": type_slug,
            },
        )

    def get_context(self, request, *args, **kwargs) -> dict:
        from poundit.models import EventType

        context = super().get_context(request, *args, **kwargs)

        upcoming = EventPage.objects.child_of(self).upcoming()
        past = EventPage.objects.child_of(self).past()

        requested_type = request.GET.get("type") if request else None
        if requested_type:
            upcoming = upcoming.of_type(requested_type)
            past = past.of_type(requested_type)

        context.update(
            {
                "upcoming": upcoming,
                "past": past,
                "featured": EventPage.objects.child_of(self).featured(),
                "event_types": EventType.objects.all(),
                "active_type": requested_type or "",
            }
        )
        return context
