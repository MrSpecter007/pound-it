from typing import override

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets import widgets
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.views.snippets import SnippetViewSet

from .service_request_hooks import _BASE_PROFILE_PANELS
from servicerequests.models import Naissance, Deuil, Relevailles, InterventionPerinatale, InterruptionGrossesse, \
    RencontresVirtuelles, ServiceProfile, BaseServiceProfile


class NaissanceModelViewSet(SnippetViewSet):
    """The view set for the Naissance model."""
    model = Naissance

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("birth_name")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


class DeuilModelViewSet(SnippetViewSet):
    """The view set for the Deuil model."""
    model = Deuil

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("deceased_name"),
        FieldPanel("deceased_date"),
        FieldPanel("additional_notes")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


class RelevaillesModelViewSet(SnippetViewSet):
    """The view set for the Relevailles model."""
    model = Relevailles

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("relevailles_note")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


class InterruptionGrossesseViewSet(SnippetViewSet):
    """The view set for the InterruptionGrossesse model."""

    model = InterruptionGrossesse

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("grossesse_note")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


class InterventionPerinataleViewSet(SnippetViewSet):
    """The view set for the InterventionPerinatale model."""
    model = InterventionPerinatale

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("intervention_perinatal_note")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


class RencontresVirtuellesViewSet(SnippetViewSet):
    """The view set for the RencontresVirtuelles model."""
    model = RencontresVirtuelles

    panels = _BASE_PROFILE_PANELS + [
        FieldPanel("rencontre_virtuelle_note")
    ]

    icon = "user"
    list_display = ("profile_code", "first_name", "last_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


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
