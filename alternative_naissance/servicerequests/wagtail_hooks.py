from django.urls import path
from wagtail import hooks
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from .models import ServiceRequest, Profile
from wagtail.snippets import widgets

from .views import share_profile


class ServiceRequestViewSet(SnippetViewSet):
    """The view set for processing service requests."""
    model = ServiceRequest
    menu_label = "Requests"
    icon = "form"
    list_display = ("name", "email", "service_type", "status", "created_at")
    list_filter = ("status", "service_type")
    search_fields = ("name", "email")


class ProfileViewSet(SnippetViewSet):
    """The view set for the main profiles created from accepting the service request."""
    model = Profile
    menu_label = "Profiles"
    icon = "user"
    list_display = ("__str__", "status")
    list_filter = ("status",)
    search_fields = ("service_request__name", "service_request__email")


# Both service requests and profiles under the same parent directory
@register_snippet
class ServiceRequestGroup(SnippetViewSetGroup):
    menu_label = "Service Requests"
    menu_icon = "folder-open-inverse"
    add_to_admin_menu = True
    items = (ServiceRequestViewSet, ProfileViewSet)


@hooks.register("register_icons")
def register_icons(icons):
    """Used for adding the share icon for specifically sharing the profile to an agent."""
    return icons + ['servicerequests/shareprofile.svg']


@hooks.register('register_admin_urls')
def register_share_profile_urls():
    return [
        path('share/profile/<int:pk>', share_profile, name='share_profile'),
    ]


# Both hooks below add the same sharing functionality, for redundancy.
@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    if type(snippet) != Profile:
        return
    snippet: Profile = snippet # to get type hint
    yield widgets.SnippetListingButton(
        'Share to An Agent',
        icon_name='shareprofile',
        url=f'/admin/share/profile/{snippet.pk}',
        priority=10
    )


class ShareProfileMenuItem(ActionMenuItem):
    """A custom action menu item for sharing a Profile with an agent."""
    name = 'action-shareprofile'
    label = "Share Profile to An Agent"
    icon_name = 'shareprofile'

    def get_url(self, context):
        return "/a url to an admin page"

    def is_shown(self, context):
        print(context)
        if context['model'] == Profile and context['view'] == 'edit':
            return True
        return False

# Displayed inside the snippet editing page
@hooks.register('register_snippet_action_menu_item')
def register_share_profile_menu_item(model):
    return ShareProfileMenuItem(order=10)