from typing import override

from django.shortcuts import redirect
from django.urls import reverse
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.views.snippets import SnippetViewSet

from servicerequests.models import ServiceRequest

_BASE_REQUEST_PANELS: list[FieldPanel] = [
    FieldPanel("status"),
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
    FieldPanel("citizenship_status")
]


class PendingByDefaultIndexView(SnippetViewSet.index_view_class):
    """
    The custom index view used by ServiceRequest to show only pending requests by default but allow the showing
    of rejected requests as well.
    """

    def get(self, request, *args, **kwargs):
        # If user did not specify that it is NOT pending in url path, redirect to path with pending enabled
        if not "status" in request.GET:
            params = request.GET.copy()
            params["status"] = "pending"
            return redirect(f"{request.path}?{params.urlencode()}")

        else:
            return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()

        request = getattr(self, "request", None)
        # If user explicitly applied a filter then let it be
        if request and "status" in request.GET:
            return qs

        # Otherwise, apply the default "pending" filter
        return qs.filter(status="pending")


class ServiceRequestViewSet(SnippetViewSet):
    """The view set for processing service requests."""

    model = ServiceRequest

    panels = [FieldPanel("service_type")] + _BASE_REQUEST_PANELS + [
        FieldPanel("status", read_only=True),
        FieldPanel("refusal_date", read_only=True),
        FieldPanel("refusal_reason"),
    ]

    menu_label = "Demandes"
    icon = "form"
    list_display = ("first_name", "last_name", "service_full_name", "status")
    list_filter = ("service_type", "status")
    search_fields = ("first_name", "last_name", "email", "phone")
    index_view_class = PendingByDefaultIndexView


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
def register_accept_request_menu_item(_model):
    return AcceptRequestMenuItem(order=20)


@hooks.register('register_snippet_action_menu_item')
def register_reject_request_menu_item(_model):
    return RejectRequestMenuItem(order=30)
