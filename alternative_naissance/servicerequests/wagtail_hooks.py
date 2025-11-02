from typing import override

from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from wagtail.snippets import widgets

from .models import ServiceRequest, BaseServiceProfile, Naissance, Deuil, ServiceProfile, InterruptionGrossesse, InterventionPerinatale, RencontresVirtuelles, Relevailles
from .views import share_profile, accept_service_request, reject_service_request, preview_profile_pdf

_BASE_PROFILE_PANELS: list[FieldPanel] = [
    FieldPanel("first_name"),
    FieldPanel("last_name"),

    FieldPanel("expected_delivery_date"),
    FieldPanel("child_birth_date"),
    FieldPanel("street_address"),
    FieldPanel("city"),
    FieldPanel("province"),
    FieldPanel("postal_code"),
    FieldPanel("no_permanent_address"),
    FieldPanel("phone"),
    FieldPanel("no_phone"),
    FieldPanel("email"),
    FieldPanel("no_email"),
    FieldPanel("languages"),
    FieldPanel("citizenship_status"),
    FieldPanel("status")
]


class ServiceRequestViewSet(SnippetViewSet):
    """The view set for processing service requests."""
    
    model = ServiceRequest

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("service_type"),
        FieldPanel("expected_delivery_date"),
        FieldPanel("child_birth_date"),
        FieldPanel("street_address"), 
        FieldPanel("city"),
        FieldPanel("province"),
        FieldPanel("postal_code"),
        FieldPanel("no_permanent_address"),
        FieldPanel("phone"),
        FieldPanel("no_phone"),
        FieldPanel("email"),
        FieldPanel("no_email"),
        FieldPanel("languages"),
        FieldPanel("citizenship_status"),
        FieldPanel("status")
    ]

    menu_label = "Demandes"
    icon = "form"
    list_display = ("first_name", "last_name", "service_full_name", "status")
    list_filter = ("status", "service_type")
    search_fields = ("first_name", "last_name", "email", "phone")


# class ProfileViewSet(SnippetViewSet):
#     """The view set for the main profiles created from accepting the service request."""
#     model = BaseServiceProfile
#
#     panels = [] + _BASE_PROFILE_PANELS
#
#     menu_label = "Profils"
#     icon = "user"
#     list_display = ("profile_code", "first_name", "last_name", "service_type", "status")
#     list_filter = ("status", "service_type")
#     search_fields = ("profile_code", "first_name", "last_name", "email", "phone")


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

##############################################


@register_snippet
class ServiceRequestGroup(SnippetViewSetGroup):
    menu_label = "Demandes de Service"
    menu_icon = "folder-open-inverse"
    add_to_admin_menu = True
    items = (
        ServiceRequestViewSet,
        # ProfileViewSet,
        NaissanceModelViewSet,
        DeuilModelViewSet,
        RelevaillesModelViewSet,
        InterruptionGrossesseViewSet,
        InterventionPerinataleViewSet,
        RencontresVirtuellesViewSet,
    )


####################################################

@hooks.register("register_icons")
def register_icons(icons):
    """Used for adding the share icon for specifically sharing the profile to an agent."""
    return icons + ['servicerequests/shareprofile.svg']


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


class AcceptRequestMenuItem(ActionMenuItem):
    """Extra action menu item in Service Request to accept a request."""
    name = 'action-acceptrequest'
    label = "Accepter la demande de service"
    icon_name = 'check'

    @override
    def get_url(self, context):
        return reverse("accept_service_request", args=(context["instance"].pk,))

    @override
    def is_shown(self, context):
        if context['model'] == ServiceRequest and context['view'] == 'edit':
            return True
        return False


class RejectRequestMenuItem(ActionMenuItem):
    """Extra action menu item in Service Request to reject a request."""
    name = 'action-rejectrequest'
    label = "Refuser la demande de service"
    icon_name = 'cross'

    @override
    def get_url(self, context):
        return reverse("reject_service_request", args=(context["instance"].pk,))

    @override
    def is_shown(self, context):
        if context['model'] == ServiceRequest and context['view'] == 'edit':
            return True
        return False


@hooks.register('register_snippet_action_menu_item')
def register_share_profile_menu_item(model):
    return ShareProfileMenuItem(order=10)


@hooks.register('register_snippet_action_menu_item')
def register_accept_request_menu_item(model):
    return AcceptRequestMenuItem(order=20)


@hooks.register('register_snippet_action_menu_item')
def register_reject_request_menu_item(model):
    return RejectRequestMenuItem(order=30)



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



@hooks.register('register_admin_urls')
def register_share_profile_urls():
    return [
        path('serviceprofiles/share/<str:profile_cls_lc>/<int:sub_id>', share_profile, name='share_profile'),
        path('serviceprofiles/preview/<str:profile_cls_lc>/<int:sub_id>', preview_profile_pdf, name='preview_profile_pdf'),
        path('servicerequests/accept-request/<int:pk>', accept_service_request, name='accept_service_request'),
        path('servicerequests/reject-request/<int:pk>', reject_service_request, name='reject_service_request'),
    ]
