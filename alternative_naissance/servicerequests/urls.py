from django.urls import path

from . import views

urlpatterns = [
    path("", views.create_service_request, name="create_service_request"),
    path("success/", views.create_service_request_success, name="create_service_request_success")
]