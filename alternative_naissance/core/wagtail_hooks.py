from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from .models import Inscription


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
