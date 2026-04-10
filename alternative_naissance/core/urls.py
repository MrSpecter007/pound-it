from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("inscription/", views.inscription_view, name="inscription"),
    path("mon-compte/", views.mon_compte_view, name="mon-compte"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("newsletter/subscribe/", views.subscribe_newsletter, name="subscribe_newsletter"),
    path("temoignages/nouveau/", views.testimonial_create, name="testimonial_create"),
]
