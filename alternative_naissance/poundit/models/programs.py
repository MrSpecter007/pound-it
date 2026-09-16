"""
Programs and the weekly schedule.

A program is the thing a dancer joins: a named crew, a technique class, an
open drop-in. It is a snippet rather than a page because it surfaces in the
schedule grid, on category listings, on the homepage and on faculty profiles;
giving each of forty crews its own URL would create thin pages nobody links to.

Schedule entries are separate rows with real ``TimeField``s, so "Mondays |
6:45 PM" is never the only machine-readable form. A program may have as many
weekly sessions as it needs.
"""

from decimal import Decimal

from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.search import index


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class TuitionPeriod(models.TextChoices):
    MONTH = "month", "per month"
    SESSION = "session", "per session"
    CLASS = "class", "per class"
    TERM = "term", "per term"
    YEAR = "year", "per year"


def format_time(value) -> str:
    """5:15 PM, not 05:15 PM."""
    if value is None:
        return ""
    return value.strftime("%I:%M %p").lstrip("0")


class ProgramQuerySet(models.QuerySet):
    def active(self) -> "ProgramQuerySet":
        return self.filter(active=True)

    def public(self) -> "ProgramQuerySet":
        """Enrollable offerings. Excludes studio rentals and private training."""
        return self.filter(active=True, is_public=True)

    def featured(self) -> "ProgramQuerySet":
        return self.public().filter(featured=True)

    def for_category(self, category) -> "ProgramQuerySet":
        slug = getattr(category, "slug", category)
        return self.public().filter(category__slug=slug)

    def for_season(self, season) -> "ProgramQuerySet":
        if season is None:
            return self.none()
        return self.filter(season=season)


class Program(ClusterableModel, index.Indexed):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    category = models.ForeignKey(
        "poundit.ProgramCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="programs",
    )
    level = models.ForeignKey(
        "poundit.TrainingLevel",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="programs",
        help_text="Drives the colour this program's classes take in the schedule grid.",
    )
    season = models.ForeignKey(
        "poundit.Season",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="programs",
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="One line, used on listings and cards.",
    )
    long_description = RichTextField(
        blank=True,
        help_text="Editorial narrative. Facts like price, age and times belong in their own fields.",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    age_label = models.CharField(
        max_length=50,
        blank=True,
        help_text='Overrides the generated label, e.g. "All ages", "18+".',
    )

    audition_required = models.BooleanField(default=False)

    tuition_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave empty when the program has several tiers; add those below instead.",
    )
    tuition_period = models.CharField(
        max_length=20,
        choices=TuitionPeriod.choices,
        blank=True,
    )
    tuition_note = models.TextField(
        blank=True,
        help_text="Anything the figure alone does not convey, e.g. what is included.",
    )

    registration_url = models.URLField(
        blank=True,
        help_text="Leave empty to fall back to the studio-wide registration URL in Pound It settings.",
    )
    registration_cta_label = models.CharField(max_length=100, blank=True)

    styles = ParentalManyToManyField(
        "poundit.DanceStyle",
        blank=True,
        related_name="programs",
    )
    faculty = ParentalManyToManyField(
        "poundit.FacultyMember",
        blank=True,
        related_name="programs",
        help_text="Who leads this program overall. Who teaches a given session is set on that session.",
    )

    competition_info = RichTextField(
        blank=True,
        help_text="Competitions, battles or performances this program takes part in.",
    )

    is_public = models.BooleanField(
        default=True,
        verbose_name="Publicly enrollable",
        help_text="Uncheck for schedule occupancy that is not an offering, such as studio rentals or private training.",
    )
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    objects = ProgramQuerySet.as_manager()

    search_fields = [
        index.SearchField("title"),
        index.SearchField("short_description"),
        index.SearchField("long_description"),
    ]

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("slug"),
                FieldPanel("category"),
                FieldPanel("hero_image"),
                FieldPanel("short_description"),
                FieldPanel("long_description"),
            ],
            heading="Basic",
        ),
        MultiFieldPanel(
            [
                FieldPanel("age_min"),
                FieldPanel("age_max"),
                FieldPanel("age_label"),
                FieldPanel("level"),
                FieldPanel("audition_required"),
            ],
            heading="Eligibility",
        ),
        MultiFieldPanel(
            [InlinePanel("schedule_entries", label="Weekly session")],
            heading="Schedule",
        ),
        MultiFieldPanel(
            [
                FieldPanel("tuition_amount"),
                FieldPanel("tuition_period"),
                InlinePanel("tuition_options", label="Additional tuition option"),
                FieldPanel("tuition_note"),
                InlinePanel("inclusions", label="What's included"),
            ],
            heading="Pricing",
        ),
        MultiFieldPanel(
            [
                FieldPanel("styles"),
                FieldPanel("faculty"),
                FieldPanel("competition_info"),
            ],
            heading="Relationships",
        ),
        MultiFieldPanel(
            [
                FieldPanel("registration_url"),
                FieldPanel("registration_cta_label"),
            ],
            heading="Registration",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_public"),
                FieldPanel("active"),
                FieldPanel("featured"),
                FieldPanel("season"),
                FieldPanel("sort_order"),
            ],
            heading="Publishing",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self) -> str:
        return self.title

    @property
    def age_display(self) -> str:
        """"Ages 6-9", "Ages 10+", "Ages 2-3", or whatever age_label overrides it with."""
        if self.age_label:
            return self.age_label
        if self.age_min and self.age_max:
            return f"Ages {self.age_min}-{self.age_max}"
        if self.age_min:
            return f"Ages {self.age_min}+"
        if self.age_max:
            return f"Up to age {self.age_max}"
        return ""

    @property
    def tuition_display(self) -> str:
        """A single figure, or the first tier when the program is tiered."""
        if self.tuition_amount is not None:
            amount = self.tuition_amount.quantize(Decimal("1")) if self.tuition_amount == self.tuition_amount.to_integral() else self.tuition_amount
            period = self.get_tuition_period_display() if self.tuition_period else ""
            return f"${amount} {period}".strip()
        first = self.tuition_options.first()
        return first.display if first else ""

    @property
    def has_tiered_tuition(self) -> bool:
        return self.tuition_options.exists()

    @property
    def level_colour(self) -> str:
        """Semantic token for the front end. Never a colour value."""
        return self.level.colour_identifier if self.level else ""

    @property
    def schedule_display(self) -> str:
        """e.g. "Mondays 5:15-6:00 PM, Wednesdays 6:00-6:45 PM"."""
        return ", ".join(
            f"{entry.get_weekday_display()}s {entry.time_display}"
            for entry in self.schedule_entries.all()
        )

    def get_registration_url(self, settings=None) -> str:
        """Program URL if set, otherwise the studio-wide default."""
        if self.registration_url:
            return self.registration_url
        return getattr(settings, "registration_url", "") if settings else ""


class ProgramInclusion(Orderable):
    """A line item in "what's included" — a performance, a costume, unlimited training."""

    program = ParentalKey(Program, related_name="inclusions", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)

    panels = [FieldPanel("text")]

    def __str__(self) -> str:
        return self.text


class ProgramTuitionOption(Orderable):
    """
    One tier of a tiered price.

    PIBA alone has five: one class a week, two a week, an unlimited pass, a
    punch pass and a drop-in rate. A single amount field cannot hold that.
    """

    program = ParentalKey(Program, related_name="tuition_options", on_delete=models.CASCADE)
    label = models.CharField(max_length=100, help_text='e.g. "Unlimited training pass".')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    period = models.CharField(max_length=20, choices=TuitionPeriod.choices, blank=True)
    note = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("label"),
        FieldPanel("amount"),
        FieldPanel("period"),
        FieldPanel("note"),
    ]

    @property
    def display(self) -> str:
        amount = self.amount.quantize(Decimal("1")) if self.amount == self.amount.to_integral() else self.amount
        period = self.get_period_display() if self.period else ""
        return f"${amount} {period}".strip()

    def __str__(self) -> str:
        return f"{self.label}: {self.display}"


class ProgramScheduleEntryQuerySet(models.QuerySet):
    def for_season(self, season) -> "ProgramScheduleEntryQuerySet":
        if season is None:
            return self.none()
        return self.filter(season=season)

    def public(self) -> "ProgramScheduleEntryQuerySet":
        return self.filter(program__active=True, program__is_public=True)

    def grid(self) -> dict:
        """
        Shape the week the way the printed schedule reads:
        ``{weekday_value: {room_id: [entries]}}``, ordered by start time.

        Templates iterate this directly rather than filtering in the template.
        """
        result: dict = {}
        entries = self.select_related("program", "room", "program__level").prefetch_related("instructors").order_by(
            "weekday", "start_time", "room__sort_order"
        )
        for entry in entries:
            room_key = entry.room_id
            result.setdefault(entry.weekday, {}).setdefault(room_key, []).append(entry)
        return result


class ProgramScheduleEntry(Orderable, ClusterableModel):
    """
    One weekly session of a program, in one room, at a real time.

    Clusterable because ``instructors`` is a ParentalManyToManyField: the
    relation has to survive being edited inside the program's InlinePanel
    before the child row has a primary key.
    """

    program = ParentalKey(Program, related_name="schedule_entries", on_delete=models.CASCADE)

    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    label = models.CharField(
        max_length=255,
        blank=True,
        help_text='Overrides the program name in the grid, e.g. "Power & Strength Training".',
    )
    room = models.ForeignKey(
        "poundit.StudioRoom",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="schedule_entries",
    )
    season = models.ForeignKey(
        "poundit.Season",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="schedule_entries",
    )
    instructors = ParentalManyToManyField(
        "poundit.FacultyMember",
        blank=True,
        related_name="schedule_entries",
        help_text="Who teaches this particular session. May differ week to week from the program's lead faculty.",
    )
    notes = models.CharField(max_length=255, blank=True)

    objects = ProgramScheduleEntryQuerySet.as_manager()

    panels = [
        FieldPanel("weekday"),
        FieldPanel("start_time"),
        FieldPanel("end_time"),
        FieldPanel("label"),
        FieldPanel("room"),
        FieldPanel("instructors"),
        FieldPanel("season"),
        FieldPanel("notes"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Weekly session"
        verbose_name_plural = "Weekly sessions"

    def __str__(self) -> str:
        return f"{self.get_weekday_display()} {self.time_display} - {self.display_label}"

    @property
    def display_label(self) -> str:
        return self.label or self.program.title

    @property
    def weekday_display(self) -> str:
        return self.get_weekday_display()

    @property
    def time_display(self) -> str:
        """"5:15-6:00 PM" — the meridiem is dropped from the start when it matches the end."""
        start = format_time(self.start_time)
        end = format_time(self.end_time)
        if start[-2:] == end[-2:]:
            start = start[:-3]
        return f"{start}-{end}"

    @property
    def duration_minutes(self) -> int:
        start = self.start_time.hour * 60 + self.start_time.minute
        end = self.end_time.hour * 60 + self.end_time.minute
        return end - start

    @property
    def instructor_display(self) -> str:
        """
        "Rico / Masha" — the form the printed schedule uses.

        Order follows each instructor's ``sort_order`` on the faculty record,
        so the studio controls who reads first without touching the session.
        """
        names = [instructor.grid_name for instructor in self.instructors.all()]
        return " / ".join(names)

    @property
    def level_colour(self) -> str:
        return self.program.level_colour
