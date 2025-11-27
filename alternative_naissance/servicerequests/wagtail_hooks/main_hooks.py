from django.urls import path
from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSetGroup

from servicerequests.views import share_profile, accept_service_request, reject_service_request, preview_profile_pdf
from .profile_hooks import InterventionPerinataleViewSet, DeuilModelViewSet, NaissanceModelViewSet, \
    InterruptionGrossesseViewSet, RencontresVirtuellesViewSet, RelevaillesModelViewSet
from .service_request_hooks import ServiceRequestViewSet


@register_snippet
class ServiceRequestGroup(SnippetViewSetGroup):
    menu_label = "Demandes de Service"
    menu_icon = "folder-open-inverse"
    add_to_admin_menu = True
    items = [
        ServiceRequestViewSet,
        # ProfileViewSet,
        NaissanceModelViewSet,
        DeuilModelViewSet,
        RelevaillesModelViewSet,
        InterruptionGrossesseViewSet,
        InterventionPerinataleViewSet,
        RencontresVirtuellesViewSet,
    ]



@hooks.register('register_admin_urls')
def register_share_profile_urls():
    return [
        path('serviceprofiles/share/<str:profile_cls_lc>/<int:sub_id>', share_profile, name='share_profile'),
        path('serviceprofiles/preview/<str:profile_cls_lc>/<int:sub_id>', preview_profile_pdf,
             name='preview_profile_pdf'),
        path('servicerequests/accept-request/<int:pk>', accept_service_request, name='accept_service_request'),
        path('servicerequests/reject-request/<int:pk>', reject_service_request, name='reject_service_request'),
    ]
