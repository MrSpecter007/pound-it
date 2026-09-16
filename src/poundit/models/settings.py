"""
Global Pound It information.

``BaseSiteSetting`` is per-site, so this lives alongside ``core.SiteSettings``
without either leaking into the other. Studio contact details, social links and
external registration URLs exist here once and are read from templates as
``{{ settings.poundit.PounditSettings.<field> }}``.
"""

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting


@register_setting
class PounditSettings(BaseSiteSetting):
    studio_name = models.CharField(max_length=255, default="Pound It Hip Hop Studios")
    tagline = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "Central Alberta\'s home of hip hop".',
    )

    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    alternate_logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Used where the primary logo does not have enough contrast.",
    )

    # Contact
    address = models.TextField(blank=True)
    maps_url = models.URLField(blank=True, help_text="Link to the studio's map listing.")
    phone_number = models.CharField(max_length=50, blank=True)
    public_email = models.EmailField(blank=True)
    opening_hours = models.TextField(
        blank=True,
        help_text='e.g. "Mon-Thu 4:00 pm - 9:00 pm".',
    )

    # External systems (Phase 1 keeps registration off-site)
    registration_url = models.URLField(
        blank=True,
        help_text="Default registration destination. Individual programs may override it.",
    )
    registration_cta_label = models.CharField(
        max_length=100,
        blank=True,
        default="Register",
        help_text="Default call-to-action label for registration buttons.",
    )
    dancer_portal_url = models.URLField(
        blank=True,
        help_text="Existing studio-management portal for current dancers.",
    )
    waiver_url = models.URLField(
        blank=True,
        help_text="Existing waiver workflow. Left external until an e-signature feature is reviewed.",
    )

    # Social
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Season
    current_season = models.ForeignKey(
        "poundit.Season",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Drives the schedule, program listings and calendar site-wide.",
    )

    # Announcement banner
    show_announcement = models.BooleanField(default=False)
    announcement_text = models.CharField(max_length=255, blank=True)
    announcement_url = models.CharField(max_length=255, blank=True)
    announcement_button_text = models.CharField(max_length=100, blank=True)

    footer_copy = models.TextField(blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("studio_name"),
                FieldPanel("tagline"),
                FieldPanel("logo"),
                FieldPanel("alternate_logo"),
            ],
            heading="Identity",
        ),
        MultiFieldPanel(
            [
                FieldPanel("address"),
                FieldPanel("maps_url"),
                FieldPanel("phone_number"),
                FieldPanel("public_email"),
                FieldPanel("opening_hours"),
            ],
            heading="Contact",
        ),
        MultiFieldPanel(
            [
                FieldPanel("registration_url"),
                FieldPanel("registration_cta_label"),
                FieldPanel("dancer_portal_url"),
                FieldPanel("waiver_url"),
            ],
            heading="Registration and external systems",
        ),
        MultiFieldPanel(
            [
                FieldPanel("instagram_url"),
                FieldPanel("facebook_url"),
                FieldPanel("tiktok_url"),
                FieldPanel("youtube_url"),
            ],
            heading="Social",
        ),
        MultiFieldPanel(
            [
                FieldPanel("current_season"),
            ],
            heading="Season",
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_announcement"),
                FieldPanel("announcement_text"),
                FieldPanel("announcement_url"),
                FieldPanel("announcement_button_text"),
            ],
            heading="Announcement banner",
        ),
        FieldPanel("footer_copy"),
    ]

    class Meta:
        verbose_name = "Pound It settings"
