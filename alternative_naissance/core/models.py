from django.db import models
from django.shortcuts import render, redirect
from wagtail.models import Page, Orderable, Site
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from modelcluster.fields import ParentalKey
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from django.core.validators import MinLengthValidator, RegexValidator
from wagtail import blocks
import uuid
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.snippets.blocks import SnippetChooserBlock
from datetime import date, timedelta

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
        InlinePanel("news_items", label="News Section"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        # récupère tous les témoignages
        context['all_testimonials'] = Testimonial.objects.all()
        return context




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
@register_snippet
class TestimonialSection(ClusterableModel):

    top_text = models.TextField(blank=True)

    panels = [
        FieldPanel("top_text"),
        InlinePanel("items", label="Témoignages"),
    ]

    def __str__(self):
        return f"Section Témoignages ({self.top_text[:30]})"
    


class Testimonial(Orderable):
    section = ParentalKey(
        "core.TestimonialSection",
        related_name="items",
        on_delete=models.CASCADE,
        null=True, blank=True
    )

    client_name = models.CharField(max_length=150, blank=True, null=True)
    client_sub_title = models.CharField(max_length=150, blank=True, null=True)
    client_text = models.TextField(blank=True)
    client_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Catégorie ou page associée à ce témoignage (ex: Naissance, Relevailles, Accueil...)"
    )

    panels = [
        FieldPanel("client_text"),
        FieldPanel("category"), 
    ]
    def __str__(self):
        return f"{self.client_name or 'Témoignage'} — {self.category or 'Général'}"
    


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
# WHY CHOOSE BLOCK
# --------------------------
class WhyChooseBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    subtitle = blocks.CharBlock(required=False)
    text = blocks.RichTextBlock(required=False, features=['bold', 'italic', 'link', 'h2', 'h3', 'ul', 'ol'])
    image = ImageChooserBlock(required=False)
    layout = blocks.ChoiceBlock(
        choices=[
            ('text_left', "Texte à gauche, Image à droite"),
            ('text_right', "Texte à droite, Image à gauche"),
        ],
        default='text_left',
        required=True
    )

    class Meta:
        template = "blocks/why_choose.html"
        icon = "placeholder"
        label = "Bloc Pourquoi nous choisir"

# --------------------------
# TESTIMONIALS CHOOSER BLOCK
# --------------------------
class TestimonialChooserBlock(blocks.StructBlock):
    section = SnippetChooserBlock(TestimonialSection)

    class Meta:
        icon = "form"
        label = "Section Témoignages"
        template = "blocks/testimonial_section.html"


# --------------------------
# BENEFIT POINT BLOCK
# --------------------------
class BenefitPointBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True, label="Texte du point")

    class Meta:
        icon = "fa-check"
        label = "Point"


class BenefitsBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True, label="Image (benefits-two__img)")
    title = blocks.CharBlock(required=True, label="Titre (section-title__title)")
    points = blocks.ListBlock(BenefitPointBlock(), label="Liste des points")

    class Meta:
        template = "blocks/benefits_block.html"
        icon = "list-ul"
        label = "Bloc : Benefits (image + titre + liste)"

# --------------------------
# PARAGRAPH BLOCK
# --------------------------
class ParagraphsBlock(blocks.StructBlock):
    paragraphs = blocks.ListBlock(
        blocks.RichTextBlock(
            features=["bold", "italic", "link"],
            label="Paragraphe"
        ),
        label="Paragraphes",
        help_text="Ajoutez un ou plusieurs paragraphes. Chaque paragraphe sera affiché dans une nouvelle ligne."
    )

    class Meta:
        template = "blocks/paragraphs_block.html"
        icon = "doc-full"
        label = "Bloc : Paragraphes multiples"

# --------------------------
# TEAM MEMBERS AND TEAM SECTION BLOCK
# --------------------------
class TeamMemberBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True, label="Image membre actuel.le.s")
    role = blocks.CharBlock(required=True, label="Rôle / Fonction (ex: Président.e)")
    name = blocks.CharBlock(required=True, label="Nom")
    facebook = blocks.URLBlock(required=False, label="Lien Facebook")
    twitter = blocks.URLBlock(required=False, label="Lien Twitter")
    linkedin = blocks.URLBlock(required=False, label="Lien LinkedIn")
    instagram = blocks.URLBlock(required=False, label="Lien Instagram")

    class Meta:
        icon = "user"
        label = "Membre de l’équipe"


class TeamSectionBlock(blocks.StructBlock):
    members = blocks.ListBlock(TeamMemberBlock())

    class Meta:
        template = "blocks/team_section.html"
        icon = "group"
        label = "Équipe"

# --------------------------
# CTA BLOCK
# --------------------------
class CTABlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, label="Titre CTA")
    phone_number = blocks.CharBlock(required=False, label="Numéro de téléphone (ex: +1 514-555-1234)")
    phone_text = blocks.CharBlock(required=False, label="Texte sous le numéro (ex: Appelez nos experts)")
    button_text = blocks.CharBlock(required=True, label="Texte du bouton")
    button_link = blocks.URLBlock(required=False, label="Lien du bouton")
    image = ImageChooserBlock(required=False, label="Image CTA")

    class Meta:
        template = "blocks/cta_block.html"
        icon = "placeholder"
        label = "Bloc CTA"

# --------------------------
# SECTION RICH TEXT BLOCK
# --------------------------
class SectionedRichTextBlock(blocks.RichTextBlock):
    class Meta:
        template = "blocks/sectioned_richtext_block.html"

# --------------------------
# LIST BLOCK TEXT BLOCK
# --------------------------
class ListPointBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True, label="Titre")

    class Meta:
        icon = "fa-check"
        label = "Point"

class ListBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, label="Titre")
    points = blocks.ListBlock(ListPointBlock(), label="Liste")

    class Meta:
        template = "blocks/list_block.html"
        icon = "list-ul"
        label = "Bloc : Liste (titre + liste)"

# --------------------------
# EVENT PAGE BLOCK
# --------------------------
class EventPage(Page):
    date = models.DateField("Date de l'événement")
    description = RichTextField(blank=True)
    link = models.URLField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("description"),
        FieldPanel("link"),
    ]

    @staticmethod
    def upcoming_events():
        """Retourne uniquement les 3 prochains mois d’événements"""
        today = date.today()
        three_months = date(today.year, today.month + 3 if today.month <= 9 else (today.month + 3) % 12, today.day)
        return EventPage.objects.live().public().filter(
            date__gte=today, date__lte=three_months
        ).order_by("date")

class CalendarBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, default="Calendrier des activités")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)

        today = date.today()
        three_months = today + timedelta(days=90)

        events_qs = EventPage.objects.live().public().filter(
            date__gte=today,
            date__lte=three_months
        ).order_by("date")

        events = [
            {
                "title": event.title,
                "start": event.date.strftime("%Y-%m-%d"),
                "url": event.url,
            }
            for event in events_qs
        ]

        # 🔑 Ajout d’un ID unique pour ce calendrier
        context["calendar_id"] = f"calendar-events-{uuid.uuid4().hex}"
        context["events"] = events
        return context

    class Meta:
        template = "blocks/calendar_block.html"
        icon = "date"
        label = "Calendrier interactif"

# --------------------------
# TABLE BLOCK
# --------------------------
class TableCellBlock(blocks.StructBlock):
    content = blocks.RichTextBlock(required=True, features=['bold', 'italic', 'link'], label="Contenu de la cellule")


    class Meta:
        icon = "doc-full"
        label = "Cellule"


class TableRowBlock(blocks.StructBlock):
    cells = blocks.ListBlock(TableCellBlock(), label="Cellules de la ligne")

    class Meta:
        icon = "grip-horizontal"
        label = "Ligne"


class DynamicTableBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, label="Titre du tableau")
    rows = blocks.ListBlock(TableRowBlock(), label="Lignes du tableau")

    class Meta:
        template = "blocks/table_block.html"
        icon = "table"
        label = "Tableau dynamique"

# --------------------------
# ATELIER BLOCK
# --------------------------
class AtelierPage(Page):
    description = RichTextField(blank=True)
    date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    lien = models.URLField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("date"),
        FieldPanel("location"),
        FieldPanel("lien"),
    ]
    subpage_types = []

    class Meta:
        verbose_name = "Page Atelier"


class AtelierListBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, help_text="Titre de la section")
    intro = blocks.TextBlock(required=False, help_text="Texte d’introduction")
    ateliers = blocks.ListBlock(
        blocks.PageChooserBlock(
            target_model="core.AtelierPage",
            help_text="Choisissez les ateliers à afficher"
        ),
        help_text="Liste d’ateliers à afficher"
    )

    class Meta:
        icon = "list-ul"
        label = "Liste d’ateliers"
        template = "blocks/atelier_list_block.html"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        raw_ateliers = value.get("ateliers", [])

        ateliers_sanitized = []
        for p in raw_ateliers:
            if not p:
                continue
            page = p.specific
            ateliers_sanitized.append({
                "title": page.title,
                "description": getattr(page, "description", ""),
                "date": getattr(page, "date", None),
                "location": getattr(page, "location", ""),
                "url": getattr(page, "url", "#"),
            })

        context["title"] = value.get("title")
        context["intro"] = value.get("intro")
        context["ateliers"] = ateliers_sanitized

        # Important : ajoute le request du parent
        if parent_context and "request" in parent_context:
            context["request"] = parent_context["request"]

        return context
    

class Inscription(models.Model):
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    courriel = models.EmailField(unique=True)
    pseudonyme = models.CharField(max_length=100, blank=True, null=True)
    mot_de_passe = models.CharField(max_length=255)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    telephone_maison = models.CharField(max_length=20, blank=True, null=True)
    cellulaire = models.CharField(max_length=20, blank=True, null=True)
    telephone_travail = models.CharField(max_length=20, blank=True, null=True)
    numero_poste = models.CharField(max_length=10, blank=True, null=True)

    # ✅ Ajoute un default
    date_inscription = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.courriel})"
    
# --------------------------
# Page générique
# --------------------------
class GenericPage(Page):
    # Page header modifiable
    header_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Titre affiché dans le page-header"
    )
    header_subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Sous-titre affiché dans le page-header"
    )
    header_background = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Image de fond du page-header"
    )

    # Contenu principal

    introduction = models.TextField(help_text="Texte d’introduction", blank=True)
    
    body = StreamField([
        ("why_choose", WhyChooseBlock()),
        ("rich_text", SectionedRichTextBlock()),
        ("testimonials", TestimonialChooserBlock()),
        ("benefits", BenefitsBlock()),
        ("benefitpoint", BenefitPointBlock()),
        ("paragraphs", ParagraphsBlock()),
        ("team", TeamSectionBlock()),
        ("cta", CTABlock()), 
        ("liste", ListBlock()),
        ("calendar_events", CalendarBlock()),
        ("dynamic_table", DynamicTableBlock()),
        ("atelier", AtelierListBlock()),
    ], 
    blank=True,
    null=True,
    default=list, 
    use_json_field=True,
    )
    

    show_page_header = models.BooleanField(
        default=True,
        verbose_name="Afficher le header de page"
    )

    content_panels = Page.content_panels + [
        FieldPanel("header_title"),
        FieldPanel("header_subtitle"),
        FieldPanel("header_background"),
        FieldPanel("show_page_header"),
        FieldPanel("introduction"),
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = "Page générique"

    template = "core/generic_page.html"

    def get_context(self, request):
        context = super().get_context(request)
        context["category"] = self.title  # ou un champ personnalisé
        return context

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
