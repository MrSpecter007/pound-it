from django.urls import path
from . import views

urlpatterns = [
    path("inscription/", views.inscription_view, name="inscription"),
    path("mon-compte/", views.mon_compte_view, name="mon_compte"),
]
