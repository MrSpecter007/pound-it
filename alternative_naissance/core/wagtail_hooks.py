from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from .models import Inscription
from .models import JobApplication


class InscriptionViewSet(ModelViewSet):
    model = Inscription
    menu_label = "Inscriptions"
    menu_icon = "user"
    icon = "user" 
    menu_order = 200
    add_to_admin_menu = True

    # ✅ Indique quels champs apparaissent dans le formulaire admin
    form_fields = ["prenom", "nom", "courriel", "ville", "date_inscription"]

    # ✅ Colonnes à afficher dans la liste
    list_display = ["prenom", "nom", "courriel", "ville", "date_inscription"]

    # ✅ Champs de recherche
    search_fields = ["prenom", "nom", "courriel"]


@hooks.register("register_admin_viewset")
def register_inscription_viewset():
    return InscriptionViewSet("inscription", url_prefix="inscription")


class JobApplicationViewSet(ModelViewSet):
    model = JobApplication

    menu_label = "Candidatures"
    menu_icon = "user"
    icon = "user"
    menu_order = 210
    add_to_admin_menu = True

    form_fields = [
        "job",
        "first_name",
        "last_name",
        "email",
        "message",
        "cv",
    ]

    list_display = [
        "first_name",
        "last_name",
        "email",
        "job",
        "cv_link",
        "created_at",
    ]

    search_fields = [
        "first_name",
        "last_name",
        "email",
    ]
    # ✅ rendre la section lecture seule
    add_view_enabled = False
    edit_view_enabled = False
    inspect_view_enabled = True


@hooks.register("register_admin_viewset")
def register_job_application_viewset():
    return JobApplicationViewSet("candidatures", url_prefix="candidatures")