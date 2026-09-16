"""
Faculty.

Instructors are snippets, not pages, because the same person appears on the
schedule grid, on program cards and on the faculty listing. Who teaches a given
session is recorded on the schedule entry rather than the program: Red Deer City
Breakers is led by different instructors on Monday and Wednesday, and Supergirlz
is co-taught, so a single program-level relation would lose that.
"""

from django.db import models
from modelcluster.fields import ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index


class FacultyMemberQuerySet(models.QuerySet):
    def active(self) -> "FacultyMemberQuerySet":
        return self.filter(active=True)

    def featured(self) -> "FacultyMemberQuerySet":
        return self.active().filter(featured=True)

    def regular(self) -> "FacultyMemberQuerySet":
        """Instructors on the weekly schedule, as opposed to occasional guests."""
        return self.active().filter(is_occasional=False)

    def occasional(self) -> "FacultyMemberQuerySet":
        return self.active().filter(is_occasional=True)


class FacultyMember(ClusterableModel, index.Indexed):
    name = models.CharField(max_length=255)
    dance_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Stage or dance name, e.g. "Dizzylock". Shown alongside the given name.',
    )
    short_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='What the schedule grid calls this person, e.g. "Nathan", "Dizzylock". '
                  "Falls back to the dance name, then the first name.",
    )
    slug = models.SlugField(max_length=255, unique=True)

    portrait = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    role = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "Studio Owner", "Dance Instructor", "Guest Instructor".',
    )

    short_bio = models.CharField(
        max_length=500,
        blank=True,
        help_text="One or two sentences for cards and listings.",
    )
    full_bio = RichTextField(blank=True)

    styles = ParentalManyToManyField(
        "poundit.DanceStyle",
        blank=True,
        related_name="faculty",
    )

    instagram_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    is_occasional = models.BooleanField(
        default=False,
        verbose_name="Occasional instructor",
        help_text="Teaches now and then rather than on the weekly schedule.",
    )
    availability_note = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "Roughly 1-2 sessions per month".',
    )

    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    objects = FacultyMemberQuerySet.as_manager()

    search_fields = [
        index.SearchField("name"),
        index.SearchField("dance_name"),
        index.SearchField("role"),
        index.SearchField("short_bio"),
        index.SearchField("full_bio"),
    ]

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("dance_name"),
                FieldPanel("short_name"),
                FieldPanel("slug"),
                FieldPanel("portrait"),
                FieldPanel("role"),
            ],
            heading="Basic",
        ),
        MultiFieldPanel(
            [
                FieldPanel("short_bio"),
                FieldPanel("full_bio"),
            ],
            heading="Biography",
        ),
        MultiFieldPanel(
            [FieldPanel("styles")],
            heading="Relationships",
        ),
        MultiFieldPanel(
            [
                FieldPanel("instagram_url"),
                FieldPanel("website_url"),
            ],
            heading="Links",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_occasional"),
                FieldPanel("availability_note"),
                FieldPanel("active"),
                FieldPanel("featured"),
                FieldPanel("sort_order"),
            ],
            heading="Publishing",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Faculty member"
        verbose_name_plural = "Faculty"

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        """"Dany Antoine (Dizzylock)" when there is a dance name, otherwise the given name."""
        if self.dance_name:
            return f"{self.name} ({self.dance_name})"
        return self.name

    @property
    def grid_name(self) -> str:
        """The short form the printed schedule uses."""
        return self.short_name or self.dance_name or self.name.split(" ")[0]

    @property
    def biography(self) -> str:
        """Whichever bio is populated, full first — the contract Codex reads."""
        return self.full_bio or self.short_bio

    @property
    def programs_taught(self):
        """
        Distinct programs this person appears against on the weekly schedule,
        whether they are listed as program faculty or only on a session.
        """
        from poundit.models import Program

        return (
            Program.objects.filter(
                models.Q(faculty=self) | models.Q(schedule_entries__instructors=self)
            )
            .distinct()
            .order_by("sort_order", "title")
        )
