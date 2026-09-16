"""
The season calendar.

The source site keeps the whole 2026-27 season as one hand-maintained list under
a "Tentative Dates" heading. Here each line is a row with real dates, a category
and a tentative flag, so the Important Dates page can be generated, sorted and
grouped rather than retyped — and so "tentative" survives as data instead of a
heading someone forgets to remove.
"""

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index


class CalendarEntryQuerySet(models.QuerySet):
    def for_season(self, season) -> "CalendarEntryQuerySet":
        if season is None:
            return self.none()
        return self.filter(season=season)

    def upcoming(self) -> "CalendarEntryQuerySet":
        today = timezone.localdate()
        return self.annotate(
            _finishes_on=models.functions.Coalesce("end_date", "start_date")
        ).filter(_finishes_on__gte=today)

    def past(self) -> "CalendarEntryQuerySet":
        today = timezone.localdate()
        return self.annotate(
            _finishes_on=models.functions.Coalesce("end_date", "start_date")
        ).filter(_finishes_on__lt=today)

    def featured(self) -> "CalendarEntryQuerySet":
        return self.filter(featured=True)

    def of_category(self, category) -> "CalendarEntryQuerySet":
        slug = getattr(category, "slug", category)
        return self.filter(category__slug=slug)

    def by_month(self) -> dict:
        """
        ``{date(year, month, 1): [entries]}`` in chronological order, which is
        how the Important Dates page reads.
        """
        import datetime

        grouped: dict = {}
        for entry in self.select_related("category").order_by("start_date"):
            key = datetime.date(entry.start_date.year, entry.start_date.month, 1)
            grouped.setdefault(key, []).append(entry)
        return grouped


class CalendarEntry(index.Indexed, models.Model):
    title = models.CharField(max_length=255)

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Only for entries spanning more than one day, such as a break or a camp.",
    )

    category = models.ForeignKey(
        "poundit.CalendarCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calendar_entries",
    )
    season = models.ForeignKey(
        "poundit.Season",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calendar_entries",
    )

    description = models.TextField(blank=True)

    related_event = models.ForeignKey(
        "poundit.EventPage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calendar_entries",
        help_text="Link to the full event page where one exists.",
    )

    is_tentative = models.BooleanField(
        default=False,
        help_text="The source calendar is published as tentative. Leave this on until the date is confirmed.",
    )
    featured = models.BooleanField(default=False)

    objects = CalendarEntryQuerySet.as_manager()

    search_fields = [
        index.SearchField("title"),
        index.SearchField("description"),
    ]

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("category"),
                FieldPanel("description"),
            ],
            heading="Basic",
        ),
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
                FieldPanel("season"),
            ],
            heading="When",
        ),
        MultiFieldPanel(
            [
                FieldPanel("related_event"),
            ],
            heading="Relationships",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_tentative"),
                FieldPanel("featured"),
            ],
            heading="Publishing",
        ),
    ]

    class Meta:
        ordering = ["start_date", "title"]
        verbose_name = "Calendar entry"
        verbose_name_plural = "Calendar entries"

    def __str__(self) -> str:
        return f"{self.date_display} - {self.title}"

    @property
    def finishes_on(self):
        return self.end_date or self.start_date

    @property
    def is_multi_day(self) -> bool:
        return self.end_date is not None and self.end_date > self.start_date

    @property
    def is_past(self) -> bool:
        return self.finishes_on < timezone.localdate()

    @property
    def date_display(self) -> str:
        """"14 September 2026", "9-12 October 2026", "21 December 2026 - 3 January 2027"."""
        start = self.start_date
        if not self.is_multi_day:
            return start.strftime("%-d %B %Y")
        end = self.end_date
        if start.year != end.year:
            return f"{start.strftime('%-d %B %Y')} - {end.strftime('%-d %B %Y')}"
        if start.month != end.month:
            return f"{start.strftime('%-d %B')} - {end.strftime('%-d %B %Y')}"
        return f"{start.strftime('%-d')}-{end.strftime('%-d %B %Y')}"

    @property
    def category_slug(self) -> str:
        return self.category.slug if self.category else ""
