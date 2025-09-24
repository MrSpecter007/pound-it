from django.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from modelcluster.fields import ParentalKey
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from wagtail.images.models import Image
from django.utils import timezone
from modelcluster.models import ClusterableModel
def today():
    return timezone.localdate()


# --------------------------
# Page d'accueil principale
# --------------------------
class CoreHomePage(Page):
    """
    Page d'accueil principale
    """
    intro = RichTextField(blank=True)

    # Options d'affichage
    show_stricky_header = models.BooleanField(default=True, verbose_name="Afficher le header sticky")
    show_counter = models.BooleanField(default=False, verbose_name="Afficher le compteur")
    show_tracking = models.BooleanField(default=False, verbose_name="Afficher le tracking")
    show_footer = models.BooleanField(default=True, verbose_name="Afficher le footer")
    show_page_header = models.BooleanField(default=False, verbose_name="Afficher le header de page")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("show_stricky_header"),
        FieldPanel("show_counter"),
        FieldPanel("show_tracking"),
        FieldPanel("show_footer"),
        FieldPanel("show_page_header"),
        InlinePanel("slides", label="Slides"),
        InlinePanel("features", label="Bloc valeurs (Accompagnement, Autonomie, Confiance)"),
        InlinePanel("about_sections", label="About sections"),
        InlinePanel("services", label="Services"),
        InlinePanel("testimonials", label="Testimonials"),
        InlinePanel("news_items", label="News Section"),
    ]




# --------------------------
# Slide pour la page d'accueil
# --------------------------
class CoreHomePageSlide(Orderable):
    """
    Slides pour CoreHomePage
    """
    page = ParentalKey(CoreHomePage, on_delete=models.CASCADE, related_name="slides")

    background_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    shape_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    title = models.CharField(max_length=250, blank=True)
    subtitle = models.CharField(max_length=250, blank=True)
    text = RichTextField(blank=True)
    button_text = models.CharField(max_length=100, blank=True)
    button_link = models.URLField(blank=True)

    panels = [
        FieldPanel("background_image"),
        FieldPanel("shape_image"),
        FieldPanel("title"),
        FieldPanel("subtitle"),
        FieldPanel("text"),
        FieldPanel("button_text"),
        FieldPanel("button_link"),
    ]

# --------------------------
# Feature Section
# --------------------------
class FeatureSection(Orderable):
    page = ParentalKey(
        "core.CoreHomePage",  # lié à ta homepage
        related_name="features",
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
    ]

# --------------------------
# Testimonial Section
# --------------------------
class TestimonialSection(Orderable, ClusterableModel):
    page = ParentalKey(
        "core.CoreHomePage",
        related_name="testimonials",
        on_delete=models.CASCADE
    )
    top_text = models.TextField(blank=True)

    panels = [
        FieldPanel("top_text"),
        InlinePanel("items", label="Témoignages"),
    ]


class Testimonial(Orderable):
    section = ParentalKey(
        "core.TestimonialSection",
        related_name="items",
        on_delete=models.CASCADE,
        null=True, blank=True  # ⚠️ important pour migrations propres
    )
    client_name = models.CharField(max_length=150)
    client_sub_title = models.CharField(max_length=150, blank=True)
    client_text = models.TextField(blank=True)
    client_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    panels = [
        FieldPanel("client_name"),
        FieldPanel("client_sub_title"),
        FieldPanel("client_text"),
        FieldPanel("client_image"),
    ]

# --------------------------
# About one section
# --------------------------
class AboutSection(Orderable):
    page = ParentalKey(
        "core.CoreHomePage",
        related_name="about_sections",
        on_delete=models.CASCADE,
    )

    image_one = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    image_two = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    subtitle = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    text_intro = RichTextField(blank=True)

    # points (sous forme de texte multi-ligne ou StreamField si tu veux plus flexible)
    point1 = models.CharField(max_length=255, blank=True)
    point2 = models.CharField(max_length=255, blank=True)
    point3 = models.CharField(max_length=255, blank=True)

    text_outro = RichTextField(blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    phone_label = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("image_one"),
        FieldPanel("image_two"),
        FieldPanel("subtitle"),
        FieldPanel("title"),
        FieldPanel("text_intro"),
        FieldPanel("point1"),
        FieldPanel("point2"),
        FieldPanel("point3"),
        FieldPanel("text_outro"),
        FieldPanel("phone_number"),
        FieldPanel("phone_label"),
    ]

# --------------------------
# News section
# --------------------------
class NewsItem(Orderable):
    page = ParentalKey(
        CoreHomePage,
        on_delete=models.CASCADE,
        related_name="news_items",
    )
    tag = models.CharField(max_length=100, blank=True)
    url = models.URLField("Lien vers l’article", blank=True)
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    panels = [
        FieldPanel("tag"),
        FieldPanel("url"),
        FieldPanel("title"),
        FieldPanel("text"),
        FieldPanel("image"),
    ]


# --------------------------
# Service one section
# --------------------------
class ServiceSection(Orderable):
    page = ParentalKey(
        "core.CoreHomePage",
        related_name="services",
        on_delete=models.CASCADE
    )

    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    # Nouveau champ pour lier vers une page interne
    link_page = models.ForeignKey(
        Page,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Choisir une page interne vers laquelle rediriger"
    )

    panels = [
        FieldPanel("image"),
        FieldPanel("title"),
        FieldPanel("description"),
        PageChooserPanel("link_page"),  # utilisé à la place de link_url
    ]


# --------------------------
# Page de contact
# --------------------------
class ContactPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

# --------------------------
# Page générique
# --------------------------
class GenericPage(Page):
    introduction = models.TextField(help_text="Texte d’introduction", blank=True)
    body = RichTextField(blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Image en mode paysage (1000px–3000px de large).",
    )

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("image"),
    ]

# --------------------------
# Paramètres du site
# --------------------------
@register_setting
class SiteSettings(BaseSiteSetting):
    site_name = models.CharField(max_length=255, default="Mon site")

    # Coordonnées
    phone_number = models.CharField(max_length=50, blank=True, help_text="Numéro de téléphone principal (ex: 514-274-1727)")
    email = models.EmailField(blank=True, help_text="Adresse email principale")

    # Réseaux sociaux
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    pinterest_url = models.URLField(blank=True, null=True)

    # Lien vers la page de contact
    contact_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Page de contact à utiliser pour le bouton dans le header"
    )

     # Texte du footer (modifiable dans l'admin)
    footer_text = models.TextField(
        blank=True, 
        null=True, 
        help_text="Texte affiché dans le footer (class footer-widget__about-text)"
    )

    # Heures d'ouverture (modifiables)
    opening_hours = models.TextField(
        blank=True,
        null=True,
        help_text="Texte affiché pour les heures d'ouverture (HTML ou texte avec <br>)"
    )

    panels = [
        FieldPanel("site_name"),
        FieldPanel("phone_number"),
        FieldPanel("email"),
        FieldPanel("facebook_url"),
        FieldPanel("twitter_url"),
        FieldPanel("instagram_url"),
        FieldPanel("pinterest_url"),
        FieldPanel("contact_page"),
        FieldPanel("footer_text"),
        FieldPanel("opening_hours"), 
    ]

    class Meta:
        verbose_name = "Paramètres du site"
