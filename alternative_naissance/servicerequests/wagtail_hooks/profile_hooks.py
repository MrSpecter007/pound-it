from typing import override, Callable

from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets import widgets
from wagtail.snippets.action_menu import ActionMenuItem
from wagtail.snippets.views.snippets import SnippetViewSet

from servicerequests.models import Naissance, Deuil, Relevailles, InterventionPerinatale, InterruptionGrossesse, \
    RencontresVirtuelles, ServiceProfile, BaseServiceProfile, ServiceStaff
from .service_request_hooks import _BASE_REQUEST_PANELS

_PLACE_OF_HOSPITAL_CHOICES = [  # Used by DatalistTextField widget
    "CHUM",
    "Glen / Victoria / Children's",
    "Hôpital Juif",
    "Lakeshore",
    "Lasalle",
    "Maisonneuve-Rosemont",
    "Sacré-Coeur",
    "Ste-Justine",
    "Ste-Mary's",
    "MDN Marie-Paule-Lanthier",
    "MDN Côte-des-Neiges",
    "MDN Anne-Courtemanche",
    "MDN Jeanne-Mance"
]

_EXPECTED_PEOPLE_AT_BIRTH_CHOICES = [  # Used by DatalistTextField widget
    "Ami.e",
    "Co-parent",
    "Co-parent absent à l’accouchement",
    "Membre de la famille",
    "Peut-être co-parent absent",
    "Peut-être membre de la famille",
]

_CHILD_CARE_PROVIDER_CHOICES = [
    "CPE",
    "Ecole",
    "Garderie privée",
    "Halte-garderie",
]

_PREGNANCY_TERMINATION_METHOD_CHOICES = [
    "Anesthésie générale",
    "Anesthésie locale",
    "Chirurgicale",
    "Médicamenteuse",
]

_BEGINNING_OF_FOLLOW_UP_CHOICES = [
    "Bébé arc-en-ciel",
    "Deuil périnatal",
    "Postnatale",
    "Prénatale",
]

_PROGRAM_CHOICES = [
    "Mesure 3.1 Faubourgs",
    "Mesure 3.1 Petite-Patrie",
    "Mesure 3.1 Villeray",
    "Mesure 3.1 Saint-Léonard",
    "Mesure 3.1 Rosemont",
    "Périnatalité",
    "Prévention Négligence CENTRE-SUD",
    "Prévention Négligence EST",
    "Prévention Négligence NIM",
    "Régulier",
    "Compte 2140 (année fiscale antérieure)",
    "Stage",
    "Marrainage",
]

_ACCOMPAGNANT_STATUS_CHOICES = [
    "Accompagnant.e",
    "Marraine",
    "Marrainé.e",
    "Relève",
    "Stagiaire",
    "Superviseur.e",
]

_PAYMENT_METHOD_CHOICES = [
    "Chèque",
    "Comptant",
    "Dépôt direct",
    "Visa",
]


class DatalistInput(forms.TextInput):
    """
    Custom text widget that shows autocomplete suggestion using <datalist> tag in HTML.
    Used for situation where the client wants a list of predefined input but also
    want a "Autre" field that  will allow custom input. So instead of having a "Choice field"
    and an extra text field that shows when picked "Autre", we will just use a simple text field
    that shows predefined suggestions.

    Note: for strings inside data_list, make sure to escape any double quotation marks
    """

    def __init__(self, data_list: list[str], name: str, data_getter_func: Callable[[], list[str]] = None, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self._data_getter_func = data_getter_func
        self.attrs.update({'list': f'list__{self._name}'})

    @override
    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs, renderer)
        data_list = f'<datalist id="list__{self._name}">'
        if self._data_getter_func:
            self._list = self._data_getter_func()
        for item in self._list:
            data_list += f'<option value="{item}">'
        data_list += '</datalist>'

        return mark_safe(text_html + data_list)


_BASE_PROFILE_HEAD_PANELS: list[FieldPanel] = [
    FieldPanel("created_at", read_only=True, help_text="Date de la accéptance de la demande de profil.")
]

_BASE_PROFILE_MIDDLE_PANELS: list[FieldPanel | MultiFieldPanel] = [
    MultiFieldPanel(heading="INFORMATIONS SUR LE.LA CLIENT.E", children=(
        FieldPanel("country_of_origin"),
        FieldPanel("quebec_arrival_date"),
        FieldPanel("age"),
        FieldPanel("occupation"),
        FieldPanel("pronouns_preferred_name"),
    )),

    MultiFieldPanel(heading="INFORMATIONS SUR LE CO_PARENT", children=(
        FieldPanel("is_monoparental"),
        FieldPanel("is_soloparental"),
        FieldPanel("is_couple"),
    )),

    # TODO: maybe make it a conditional field instead
    MultiFieldPanel(heading="INFORMATIONS SUR LE/LA PARTENAIRE (Si applicable)", children=(
        FieldPanel("partner_full_name"),
        FieldPanel("partner_email"),
        FieldPanel("partner_occupation"),
        FieldPanel("partner_absent_from_quebec"),
    )),
]

_BASE_PROFILE_END_PANELS: list[FieldPanel] = [
    MultiFieldPanel(heading="CONFIDENTIALITÉ ET STATISTIQUES", children=(
        FieldPanel("consent_share_personal_info"),
        FieldPanel("consent_statistic_collection"),
    )),

    MultiFieldPanel(heading="AUTRES INFORMATIONS", children=(
        FieldPanel("vulnerability_criteria_for_program_admission"),
        FieldPanel("other_notes"),
    )),

    FieldPanel("program", widget=DatalistInput(_PROGRAM_CHOICES, "program")),

    MultiFieldPanel(heading="DON ET EVALUATION", children=(
        FieldPanel("solicited_for_donation"),
        FieldPanel("solicited_for_evaluation"),
        FieldPanel("donation_date"),
        FieldPanel("donation_amount"),
        FieldPanel("donation_receipt_number"),
        FieldPanel("donation_payment_method"),
    )),

    FieldPanel("general_notes"),
]

_ACCOMPAGNANT_PANELS: list[FieldPanel | MultiFieldPanel] = [
    MultiFieldPanel(heading="ACCOMPAGNANT.E PRINCIPAL.E", children=(
        FieldPanel("principle_accompanying_person",
                   widget=DatalistInput([], "principle_accompanying_person",
                                        ServiceStaff.get_accompagnant_service_staff_names)),
        FieldPanel("principle_status",
                   widget=DatalistInput(_ACCOMPAGNANT_STATUS_CHOICES, "principle_status")),
        FieldPanel("principle_trainee_paid_amount"),
        FieldPanel("principle_balance_sheet_submission_date"),
        FieldPanel("principle_amount_paid"),
        FieldPanel("principle_payment_method", widget=DatalistInput(_PAYMENT_METHOD_CHOICES, "principle_payment_method")),
    )),

    MultiFieldPanel(heading="ACCOMPAGNANT.E SECONDAIRE", children=(
        FieldPanel("secondary_accompanying_person",
                   widget=DatalistInput([], "secondary_accompanying_person",
                                        ServiceStaff.get_accompagnant_service_staff_names)),
        FieldPanel("secondary_status",
                   widget=DatalistInput(_ACCOMPAGNANT_STATUS_CHOICES, "secondary_status")),
        FieldPanel("secondary_trainee_paid_amount"),
        FieldPanel("secondary_balance_sheet_submission_date"),
        FieldPanel("secondary_amount_paid"),
        FieldPanel("secondary_payment_method", widget=DatalistInput(_PAYMENT_METHOD_CHOICES, "secondary_payment_method")),
    )),

]

_BASE_PROFILE_LIST_DISPLAY: list[str] = ["profile_code", "first_name", "last_name", "status", "tax_year"]
_BASE_PROFILE_SEARCH_FIELDS: list[str] = ["profile_code", "first_name", "last_name", "email", "phone", "tax_year"]


class NaissanceModelViewSet(SnippetViewSet):
    """The view set for the Naissance model."""
    model = Naissance

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("anticipated_new_born_delivery_date"),
            FieldPanel("place_of_delivery",
                       widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "place_of_delivery")),
            FieldPanel("follow_up_by"),
            FieldPanel("referred_by"),
            FieldPanel("expected_people_at_childbirth",
                       widget=DatalistInput(_EXPECTED_PEOPLE_AT_BIRTH_CHOICES, "expected_people_at_childbirth")),
            FieldPanel("comments_on_childbirth"),
            FieldPanel("service_expectations"),
            FieldPanel("pregnancy_conditions"),
            FieldPanel("pregnancy_concerns"),
            FieldPanel("birth_concerns"),
            FieldPanel("baby_arrival_concerns"),
            FieldPanel("has_prenatal_classes"),
            FieldPanel("prenatal_classes_notes"),
        )),
    ] + _ACCOMPAGNANT_PANELS + _BASE_PROFILE_END_PANELS)
    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class DeuilModelViewSet(SnippetViewSet):
    """The view set for the Deuil model."""
    model = Deuil

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET L'INTERRUPTION (Deuil et IG)", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children_exclude_deceased"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("date_or_expected_date_of_event"),
            FieldPanel("place", widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "place")),
            FieldPanel("event_description"),
            FieldPanel("special_condition"),
            FieldPanel("service_expectations"),
            FieldPanel("referred_by"),

        ))
    ] + _ACCOMPAGNANT_PANELS + _BASE_PROFILE_END_PANELS)

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class RelevaillesModelViewSet(SnippetViewSet):
    """The view set for the Relevailles model."""
    model = Relevailles

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S (Relevailles)", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("child_care_provider",
                       widget=DatalistInput(_CHILD_CARE_PROVIDER_CHOICES, "child_care_provider")),
            FieldPanel("new_born_delivery_date"),
            FieldPanel("pregnancy_and_child_birth_progress"),
            FieldPanel("place_of_delivery",
                       widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "place_of_delivery")),
            FieldPanel("breastfeeding"),
            FieldPanel("referred_by"),
            FieldPanel("postnatal_condition"),
            FieldPanel("service_expectations"),
        ))
    ] + _ACCOMPAGNANT_PANELS + _BASE_PROFILE_END_PANELS)

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class InterruptionGrossesseViewSet(SnippetViewSet):
    """The view set for the InterruptionGrossesse model."""

    model = InterruptionGrossesse

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET L'INTERRUPTION (Deuil et IG)", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children_exclude_deceased"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("date_or_expected_date_of_event"),
            FieldPanel("place", widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "place")),
            FieldPanel("gestational_age"),
            FieldPanel("pregnancy_termination_method",
                       widget=DatalistInput(_PREGNANCY_TERMINATION_METHOD_CHOICES, "pregnancy_termination_method")),
            FieldPanel("event_description"),
            FieldPanel("special_condition"),
            FieldPanel("service_expectations"),
            FieldPanel("referred_by"),
        ))
    ] + _ACCOMPAGNANT_PANELS + _BASE_PROFILE_END_PANELS)

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class InterventionPerinataleViewSet(SnippetViewSet):
    """The view set for the InterventionPerinatale model."""
    model = InterventionPerinatale

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("beginning_of_follow_up",
                       widget=DatalistInput(_BEGINNING_OF_FOLLOW_UP_CHOICES, "beginning_of_follow_up")),
            FieldPanel("referred_by"),
            FieldPanel("anticipated_new_born_delivery_date"),
            FieldPanel("birth_date"),
            FieldPanel("date_or_expected_date_of_event"),
            FieldPanel("birth_place",
                       widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "birth_place")),
            FieldPanel("follow_up_by"),
            FieldPanel("expected_people_at_childbirth",
                       widget=DatalistInput(_EXPECTED_PEOPLE_AT_BIRTH_CHOICES, "expected_people_at_childbirth")),
            FieldPanel("special_conditions"),
            FieldPanel("pregnancy_related_concerns"),
            FieldPanel("service_expectations"),
            FieldPanel("postnatal_needs"),
            FieldPanel("community_resources"),
            FieldPanel("support_network"),
        )),

        MultiFieldPanel(heading="NTERVENANT.E PRINCIPAL.E", children=(
            FieldPanel("principle_intervenant_person",
                       widget=DatalistInput([], "principle_intervention_person",
                                            ServiceStaff.get_intervenant_service_staff_names)
                       ),
        ))
    ] + _BASE_PROFILE_END_PANELS)

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


class RencontresVirtuellesViewSet(SnippetViewSet):
    """The view set for the RencontresVirtuelles model."""
    model = RencontresVirtuelles

    panels = (_BASE_PROFILE_HEAD_PANELS + _BASE_REQUEST_PANELS + _BASE_PROFILE_MIDDLE_PANELS + [
        MultiFieldPanel(heading="INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S", children=(
            FieldPanel("number_of_pregnancies"),
            FieldPanel("number_of_children"),
            InlinePanel(relation_name="children", label="Information sur l'enfant", max_num=10, min_num=0),
            FieldPanel("anticipated_new_born_delivery_date"),
            FieldPanel("place_of_delivery",
                       widget=DatalistInput(_PLACE_OF_HOSPITAL_CHOICES, "place_of_delivery")),
            FieldPanel("follow_up_by"),
            FieldPanel("referred_by"),
            FieldPanel("expected_people_at_childbirth",
                       widget=DatalistInput(_EXPECTED_PEOPLE_AT_BIRTH_CHOICES, "expected_people_at_childbirth")),
            FieldPanel("comments_on_childbirth"),
            FieldPanel("service_expectations"),
            FieldPanel("pregnancy_conditions"),
            FieldPanel("pregnancy_concerns"),
            FieldPanel("birth_concerns"),
            FieldPanel("baby_arrival_concerns"),
            FieldPanel("has_prenatal_classes"),
            FieldPanel("prenatal_classes_notes"),
        )),
    ] + _ACCOMPAGNANT_PANELS + _BASE_PROFILE_END_PANELS)

    icon = "user"
    list_display = _BASE_PROFILE_LIST_DISPLAY
    list_filter = ("status", "service_type")
    search_fields = _BASE_PROFILE_SEARCH_FIELDS


#################### Create and register main custom buttons


class ShareProfileMenuItem(ActionMenuItem):
    """A custom action menu item for sharing a Profile with an agent."""
    name = 'action-shareprofile'
    label = "Partager le profil avec un agent."
    icon_name = 'shareprofile'

    @override
    def get_url(self, context):
        instance: ServiceProfile = context["instance"]
        profile_cls_lc: str = instance.__class__.__name__.lower()
        return reverse("share_profile", args=(profile_cls_lc, context["instance"].sub_id,))

    @override
    def is_shown(self, context):
        if issubclass(context['model'], BaseServiceProfile) and context['view'] == 'edit':
            return True
        return False


@hooks.register('register_snippet_action_menu_item')
def register_share_profile_menu_item(model):
    return ShareProfileMenuItem(order=10)


########## Create share profile button also in the listing menus.
@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    """ For Profiles, add a button to share the profile to an agent."""
    if not issubclass(type(snippet), BaseServiceProfile):
        return
    snippet: ServiceProfile = snippet  # to get type hint
    profile_cls_lc: str = snippet.__class__.__name__.lower()
    yield widgets.SnippetListingButton(
        'Share to An Agent',
        icon_name='shareprofile',
        url=reverse("share_profile", args=(profile_cls_lc, snippet.sub_id,)),
        priority=10
    )
