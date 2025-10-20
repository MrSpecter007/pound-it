from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("inscription/", views.inscription_view, name="inscription"),
    path("mon-compte/", views.mon_compte_view, name="mon-compte"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
]
