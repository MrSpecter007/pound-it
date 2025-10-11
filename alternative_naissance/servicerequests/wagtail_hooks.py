from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .models import ServiceRequest, Profile
from wagtail.snippets import widgets

from .views import share_profile, accept_service_request, reject_service_request, preview_profile_pdf


class ServiceRequestViewSet(SnippetViewSet):
    """The view set for processing service requests."""
    model = ServiceRequest

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("email"),
        FieldPanel("service_type"),
    ]

    menu_label = "Demandes"
    icon = "form"
    list_display = ("email", "first_name", "last_name", "service_type")
    list_filter = ("status", "service_type")
    search_fields = ("first_name", "last_name", "email")


class ProfileViewSet(SnippetViewSet):
    """The view set for the main profiles created from accepting the service request."""
    model = Profile

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("email"),
        FieldPanel("service_type"),
        FieldPanel("address"),
        FieldPanel("age"),
        FieldPanel("immigration_status"),

        FieldPanel("status"),
    ]

    menu_label = "Profiles"
    icon = "user"
    list_display = ("email", "first_name", "last_name", "service_type", "status")
    list_filter = ("status", "service_type", "status")
    search_fields = ("first_name", "last_name", "email")


##############################################


# Both service requests and profiles under the same parent directory
@register_snippet
class ServiceRequestGroup(SnippetViewSetGroup):
    menu_label = "Service Requests"
    menu_icon = "folder-open-inverse"
    add_to_admin_menu = True
    items = (ServiceRequestViewSet, ProfileViewSet)


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

    def get_url(self, context):
        return reverse("share_profile", args=(context["instance"].pk,))

    def is_shown(self, context):
        print(context)
        if context['model'] == Profile and context['view'] == 'edit':
            return True
        return False


class AcceptRequestMenuItem(ActionMenuItem):
    """Extra action menu item in Service Request to accept a request."""
    name = 'action-acceptrequest'
    label = "Accepter la demande de service"
    icon_name = 'check'

    def get_url(self, context):
        return reverse("accept_service_request", args=(context["instance"].pk,))

    def is_shown(self, context):
        if context['model'] == ServiceRequest and context['view'] == 'edit':
            return True
        return False


class RejectRequestMenuItem(ActionMenuItem):
    """Extra action menu item in Service Request to reject a request."""
    name = 'action-rejectrequest'
    label = "Refuser la demande de service"
    icon_name = 'cross'

    def get_url(self, context):
        return reverse("reject_service_request", args=(context["instance"].pk,))

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
    if type(snippet) != Profile:
        return
    snippet: Profile = snippet  # to get type hint
    yield widgets.SnippetListingButton(
        'Share to An Agent',
        icon_name='shareprofile',
        url=reverse("share_profile", args=(snippet.pk,)),
        priority=10
    )



@hooks.register('register_admin_urls')
def register_share_profile_urls():
    return [
        path('serviceprofiles/share/<int:pk>', share_profile, name='share_profile'),
        path('serviceprofiles/preview/<int:pk>', preview_profile_pdf, name='preview_profile_pdf'),
        path('servicerequests/accept/<int:pk>', accept_service_request, name='accept_service_request'),
        path('servicerequests/reject/<int:pk>', reject_service_request, name='reject_service_request'),
    ]
