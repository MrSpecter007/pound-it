"""
Reusable taxonomies for Pound It.

These are the vocabularies that programs, schedule entries, faculty, events
and calendar entries relate to. They are snippets rather than ``choices``
fields so studio staff can edit them without a developer, and so templates
never hardcode an identifier.
"""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index


class TaxonomyBase(models.Model):
    """Shared shape for every Pound It vocabulary: a name, a stable slug, an order."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Stable identifier used by templates. Avoid changing it once content references it.",
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )

    class Meta:
        abstract = True
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Season(models.Model):
    """
    A studio season, e.g. "2026/2027".

    Programs, schedule entries and calendar entries hang off a season so the
    whole site can roll over without deleting last year's data.
    """

    label = models.CharField(
        max_length=50,
        unique=True,
        help_text='Displayed as-is, e.g. "2026/2027".',
    )
    slug = models.SlugField(max_length=50, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(
        default=False,
        help_text="Exactly one season should be current. Setting this unsets the others.",
    )

    panels = [
        FieldPanel("label"),
        FieldPanel("slug"),
        FieldPanel("start_date"),
        FieldPanel("end_date"),
        FieldPanel("is_current"),
    ]

    class Meta:
        ordering = ["-start_date", "-label"]
        verbose_name = "Season"
        verbose_name_plural = "Seasons"

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if self.is_current:
            Season.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)

    @classmethod
    def current(cls) -> "Season | None":
        return cls.objects.filter(is_current=True).first()


class DanceStyle(TaxonomyBase, index.Indexed):
    """A street or club dance style taught at the studio."""

    short_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="One line, used on style listings.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("short_description"),
        FieldPanel("sort_order"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("short_description"),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Dance style"
        verbose_name_plural = "Dance styles"


class TrainingLevel(TaxonomyBase):
    """
    A row of the studio's schedule legend.

    ``colour_identifier`` is semantic, never a hex value. The front end maps
    these slugs to visual tokens, so the palette can change without a migration.
    """

    display_label = models.CharField(
        max_length=100,
        help_text='Label shown in the schedule legend, e.g. "PIBA (Adults)".',
    )
    colour_identifier = models.SlugField(
        max_length=50,
        unique=True,
        help_text='Semantic token for the front end, e.g. "crew", "piba", "open". Not a colour value.',
    )
    description = models.CharField(max_length=255, blank=True)
    age_label = models.CharField(
        max_length=50,
        blank=True,
        help_text='Human-readable age range, e.g. "Ages 6-9".',
    )
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    show_in_legend = models.BooleanField(
        default=True,
        help_text="Uncheck to colour the schedule grid with this level without listing it in the public legend.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("slug"),
                FieldPanel("display_label"),
                FieldPanel("colour_identifier"),
            ],
            heading="Identity",
        ),
        MultiFieldPanel(
            [
                FieldPanel("description"),
                FieldPanel("age_label"),
                FieldPanel("age_min"),
                FieldPanel("age_max"),
            ],
            heading="Eligibility",
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_in_legend"),
                FieldPanel("sort_order"),
            ],
            heading="Display",
        ),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Training level"
        verbose_name_plural = "Training levels"


class ProgramCategory(TaxonomyBase):
    """Top-level grouping for programs: kids and teen, adult, competitive, open training."""

    short_description = models.TextField(
        blank=True,
        help_text="Intro copy for this category's listing.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("short_description"),
        FieldPanel("sort_order"),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Program category"
        verbose_name_plural = "Program categories"


class StudioRoom(TaxonomyBase):
    """
    A physical room at the studio.

    The weekly schedule runs two rooms in parallel, so room is a column of the
    grid rather than an incidental note.
    """

    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to retire a room without deleting its history.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("is_active"),
        FieldPanel("sort_order"),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Studio room"
        verbose_name_plural = "Studio rooms"


class EventType(TaxonomyBase):
    """Battles, workshops, camps, performances, competitions, festivals, intensives."""

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("sort_order"),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Event type"
        verbose_name_plural = "Event types"


class CalendarCategory(TaxonomyBase):
    """Classifies season calendar entries: class days, closures, battles, shows, and so on."""

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("sort_order"),
    ]

    class Meta(TaxonomyBase.Meta):
        verbose_name = "Calendar category"
        verbose_name_plural = "Calendar categories"
