
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import FieldPanel
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField


class HomePage(Page):
    intro = RichTextField(blank=True)

    # Nouveaux champs pour contrôler l’affichage
    show_stricky_header = models.BooleanField(default=True, verbose_name="Afficher le header sticky")
    show_counter = models.BooleanField(default=False, verbose_name="Afficher le compteur")
    show_tracking = models.BooleanField(default=False, verbose_name="Afficher le tracking")
    show_footer = models.BooleanField(default=True, verbose_name="Afficher le footer")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("show_stricky_header"),
        FieldPanel("show_counter"),
        FieldPanel("show_tracking"),
        FieldPanel("show_footer"),
    ]

class ContactPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

@register_setting
class SiteSettings(BaseSiteSetting):
    contact_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    panels = [
        FieldPanel("contact_page"),
    ]