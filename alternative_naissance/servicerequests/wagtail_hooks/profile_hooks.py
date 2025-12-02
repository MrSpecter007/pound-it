from typing import override

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets import widgets
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.views.snippets import SnippetViewSet

from .service_request_hooks import _BASE_REQUEST_PANELS
from servicerequests.models import Naissance, Deuil, Relevailles, InterventionPerinatale, InterruptionGrossesse, \
    RencontresVirtuelles, ServiceProfile, BaseServiceProfile

_BASE_PROFILE_HEAD_PANELS: list[FieldPanel] = [
    FieldPanel("created_at", read_only=True, help_text="Date de la accéptance de la demande de profil.")
]

_BASE_PROFILE_MIDDLE_PANELS: list[FieldPanel | MultiFieldPanel] = [
    MultiFieldPanel(heading="INFORMATIONS SUR LE.LA CLIENT.E", children=(
        FieldPanel("country_of_origin"),
        FieldPanel("quebec_arrival_date"),
        FieldPanel("age"),
        FieldPanel("occupation"),
        FieldPanel("pronouns_preferred_name"),
    )),

    MultiFieldPanel(heading="INFORMATIONS SUR LE CO_PARENT", children=(
        FieldPanel("is_monoparental"),
        FieldPanel("is_soloparental"),
        FieldPanel("is_couple"),
    )),

    # TODO: maybe make it a conditional field instead
    MultiFieldPanel(heading="INFORMATIONS SUR LE/LA PARTENAIRE (Si applicable)", children=(
        FieldPanel("partner_full_name"),
        FieldPanel("partner_email"),
        FieldPanel("partner_occupation"),
        FieldPanel("partner_absent_from_quebec"),
    )),
]

_BASE_PROFILE_LIST_DISPLAY: list[str] = ["profile_code", "first_name", "last_name", "status", "tax_year"]
_BASE_PROFILE_SEARCH_FIELDS: list[str] = ["profile_code", "first_name", "last_name", "email", "phone", "tax_year"]


class NaissanceModelViewSet(SnippetViewSet):
    """The view set for the Naissance model."""
    model = Naissance

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        FieldPanel("birth_name")
    ])

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class DeuilModelViewSet(SnippetViewSet):
    """The view set for the Deuil model."""
    model = Deuil

    panels = _BASE_REQUEST_PANELS + [
        FieldPanel("deceased_name"),
        FieldPanel("deceased_date"),
        FieldPanel("additional_notes")
    ]

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class RelevaillesModelViewSet(SnippetViewSet):
    """The view set for the Relevailles model."""
    model = Relevailles

    panels = _BASE_REQUEST_PANELS + [
        FieldPanel("relevailles_note")
    ]

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class InterruptionGrossesseViewSet(SnippetViewSet):
    """The view set for the InterruptionGrossesse model."""

    model = InterruptionGrossesse

    panels = _BASE_REQUEST_PANELS + [
        FieldPanel("grossesse_note")
    ]

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class InterventionPerinataleViewSet(SnippetViewSet):
    """The view set for the InterventionPerinatale model."""
    model = InterventionPerinatale

    panels = _BASE_REQUEST_PANELS + [
        FieldPanel("intervention_perinatal_note")
    ]

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class RencontresVirtuellesViewSet(SnippetViewSet):
    """The view set for the RencontresVirtuelles model."""
    model = RencontresVirtuelles

    panels = _BASE_REQUEST_PANELS + [
        FieldPanel("rencontre_virtuelle_note")
    ]

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


#################### Create and register main custom buttons

class ShareProfileMenuItem(ActionMenuItem):
    """A custom action menu item for sharing a Profile with an agent."""
    name = 'action-shareprofile'
    label = "Partager le profil avec un agent."
    icon_name = 'shareprofile'

    @override
    def get_url(self, context):
        instance: ServiceProfile = context["instance"]
        profile_cls_lc: str = instance.__class__.__name__.lower()
        return reverse("share_profile", args=(profile_cls_lc, context["instance"].sub_id,))

    @override
    def is_shown(self, context):
        if issubclass(context['model'], BaseServiceProfile) and context['view'] == 'edit':
            return True
        return False




@hooks.register('register_snippet_action_menu_item')
def register_share_profile_menu_item(model):
    return ShareProfileMenuItem(order=10)



########## Create share profile button also in the listing menus.
@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    """ For Profiles, add a button to share the profile to an agent."""
    if not issubclass(type(snippet), BaseServiceProfile):
        return
    snippet: ServiceProfile = snippet  # to get type hint
    profile_cls_lc: str = snippet.__class__.__name__.lower()
    yield widgets.SnippetListingButton(
        'Share to An Agent',
        icon_name='shareprofile',
        url=reverse("share_profile", args=(profile_cls_lc, snippet.sub_id,)),
        priority=10
    )
