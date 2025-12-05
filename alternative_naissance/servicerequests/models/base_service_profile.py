from typing import Any

from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable

from .shared_properties import _SERVICE_CHOICES, _LANGUAGE_CHOICES, _CITIZENSHIP_STATUS_CHOICES, ProfileCodePrefix


class BaseServiceProfile(ClusterableModel, models.Model):
    """The Profile model mirrors all the information in the ServiceRequest model, and adds additional fields."""
    SERVICE_CHOICES = _SERVICE_CHOICES
    LANGUAGE_CHOICES = _LANGUAGE_CHOICES
    CITIZENSHIP_STATUS_CHOICES = _CITIZENSHIP_STATUS_CHOICES

    STATUS_CHOICES = [
        ("complete", "Dossier complet"),
        ("incomplete", "Dossier incomplet"),
        ("problematic", "Dossier problématique"),
        ("finished", "Dossier terminé"),
        ("canceled", "Dossier annulé")
    ]

    ############### START OF PART NOT SHARED WITH AGENT !! ###############
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")
    created_at = models.DateTimeField(auto_now_add=True)
    ############### END OF PART NOT SHARED WITH AGENT !! ###############

    ########## Basic information
    first_name = models.CharField(max_length=255, verbose_name="Prénom")
    last_name = models.CharField(max_length=255, verbose_name="Nom")

    # Service type and conditional fields
    # The service type will be not actually be used to determine the profile type on the code level, it is here simply for convenience
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES,
                                    verbose_name="Type de Service")

    # Conditional fields based on service type
    expected_delivery_date = models.DateField(null=True, blank=True,
                                              verbose_name="Date prévue d'accouchement")
    child_birth_date = models.DateField(null=True, blank=True,
                                        verbose_name="Date de naissance")

    # Address fields
    street_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ville")
    province = models.CharField(max_length=100, null=True, blank=True, verbose_name="Province")
    postal_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="Code postal")
    no_permanent_address = models.BooleanField(default=False, verbose_name="Pas d'adresse permanente")

    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone principal")
    no_phone = models.BooleanField(default=False, verbose_name="Pas de téléphone")

    email = models.EmailField(blank=True, null=True, verbose_name="Courriel")
    no_email = models.BooleanField(default=False, verbose_name="Pas de courriel")

    # Languages spoken (stored as comma-separated values)
    languages = models.CharField(max_length=255, verbose_name="Langue(s) parlée(s)")

    # Citizenship status
    citizenship_status = models.CharField(max_length=100, choices=CITIZENSHIP_STATUS_CHOICES,
                                          verbose_name="Statut de citoyenneté")

    ################# Shared fields that are not from service request ######################
    ######## INFORMATIONS SUR LE.LA CLIENT.E à tous les formulaires #######
    country_of_origin = models.CharField(max_length=255, null=True, blank=True, verbose_name="Pays d'origine")
    quebec_arrival_date = models.DateField(null=True, blank=True, verbose_name="Date d'arrivée au Québec")
    age = models.IntegerField(null=True, blank=True, verbose_name="Âge")
    occupation = models.CharField(max_length=255, null=True, blank=True, verbose_name="Occupation")
    pronouns_preferred_name = models.CharField(max_length=255, null=True, blank=True,
                                               verbose_name="Pronoms ou nom de préférence")

    ####### INFORMATIONS SUR LE CO-PARENT à tous les formulaires #######
    is_monoparental = models.BooleanField(default=False, verbose_name="Monoparentale")
    is_soloparental = models.BooleanField(default=False, verbose_name="Soloparentale")
    is_couple = models.BooleanField(default=False, verbose_name="Couple")

    # Partner information (only used if is_couple=True)
    partner_full_name = models.CharField(max_length=255, null=True, blank=True,
                                         verbose_name="Prénom, nom du partenaire")
    partner_email = models.EmailField(null=True, blank=True, verbose_name="Courriel du partenaire")
    partner_occupation = models.CharField(max_length=255, null=True, blank=True,
                                          verbose_name="Occupation du partenaire")
    partner_absent_from_quebec = models.BooleanField(default=False, verbose_name="Partenaire absent(e) du Québec")

    ############### START OF PART NOT SHARED WITH AGENT !! ###############
    ##### CONFIDENTIALITÉ ET STATISTIQUES
    consent_share_personal_info = models.BooleanField(null=True, blank=True,
                                                      verbose_name="Consentement sur le partage des informations personnelles",
                                                      help_text="Acceptez-vous qu’Alternative Naissance partage les informations recueillies pour cette demande de service avec l’accompagnant.e qui sera responsable de votre suivi, ainsi que sa relève? ")

    consent_statistic_collection = models.BooleanField(null=True, blank=True, verbose_name="Statistiques", help_text="""
    Acceptez-vous qu’Alternative Naissance compile certaines données relatives à votre suivi et à votre accouchement, de manière anonyme et confidentielle, pour des fins statistiques? 

    Ces données pourraient ensuite être utilisées pour évaluer les effets de notre pratique et avoir un portrait de certaines pratiques obstétricales et de leurs effets.
    """)

    #### AUTRES INFORMATIONS
    vulnerability_criteria_for_program_admission = models.TextField(null=True, blank=True,
                                                                    verbose_name="Critères de vulnérabilité pour admissibilité aux programmes")
    other_notes = models.TextField(null=True, blank=True, verbose_name="Autres notes (Coordo services")
    ############### END OF PART NOT SHARED WITH AGENT !! ###############

    ####### PROGRAMME à tous les formulaires #######
    program = models.CharField(max_length=255, null=True, blank=True, verbose_name="Programme")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        """
        The profile code prefix is a unique combination of capital letters that correspond to the service type. Appended before the unique ID.

        Each subclass of Profile must implement this property to return the profile code prefix. The default implementation
        in the Profile class is just an empty string to avoid errors, but it should never be called in theory.

        Example: N for Naissance profiles, D for Deuil profiles, etc.
        """
        return ProfileCodePrefix.BASE_PROFILE

    @property
    def profile_code(self) -> str:
        """
        The profile code is the business facing ID for each profile. It is generated by combining the service code with
        the sub unique id of each sub class. Example, N-000001 for Naissance profiles and D-000001 for Deuil profiles. The
        code suffix number is padded with zeros to ensure a consistent length and only has to be unique within the subclass.

        Each subclass of Profile must implement this method to return a unique ID within a service type. The default
        implementation in the Profile class should never be called in theory.
        """
        # TODO Should probably remove default implementation and use `pass` instead
        return str(self.id).zfill(7)

    @property
    def tax_year(self) -> str:
        """The tax year which the profile belongs to. NOT SENT TO THE AGENT."""
        date = self.created_at.date()
        # Note that in edge case of a request was made at exactly April 1st 0h0m0s0ms, is supposed to be in the previous tax year (how it works in the report functionality).
        # But here it would've been categorized as the current tax year. This is so unlikely to happen that it is left as is for now.
        if date.month < 4:
            return str(date.year - 1) + " - " + str(date.year)
        else:
            return str(date.year) + " - " + str(date.year + 1)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        """
        Returns a list of lists containing the field name and value for each field needed by the agent.

        Will be used by the PDF generation function to generate the PDF.

        ALL MODELS that extend the Profile model MUST implement this method as add additional fields to the PDF.
        """
        return [
            ["Numero du dossier", self.profile_code],
            [self._meta.get_field("first_name").verbose_name, self.first_name],
            [self._meta.get_field("last_name").verbose_name, self.last_name],

            [self._meta.get_field("service_type").verbose_name,
             dict(self.SERVICE_CHOICES).get(self.service_type, self.service_type)],

            [self._meta.get_field("expected_delivery_date").verbose_name, self.expected_delivery_date],
            [self._meta.get_field("child_birth_date").verbose_name, self.child_birth_date],

            [self._meta.get_field("street_address").verbose_name, self.street_address],
            [self._meta.get_field("city").verbose_name, self.city],
            [self._meta.get_field("province").verbose_name, self.province],
            [self._meta.get_field("postal_code").verbose_name, self.postal_code],
            [self._meta.get_field("no_permanent_address").verbose_name, self.no_permanent_address],

            [self._meta.get_field("phone").verbose_name, self.phone],
            [self._meta.get_field("no_phone").verbose_name, self.no_phone],

            [self._meta.get_field("email").verbose_name, self.email],
            [self._meta.get_field("no_email").verbose_name, self.no_email],

            [self._meta.get_field("languages").verbose_name, self.languages],

            [self._meta.get_field("citizenship_status").verbose_name,
             dict(self.CITIZENSHIP_STATUS_CHOICES).get(self.citizenship_status, self.citizenship_status)],

            ##### INFORMATION SUR LE CLIENT
            [self._meta.get_field("country_of_origin").verbose_name, self.country_of_origin],
            [self._meta.get_field("quebec_arrival_date").verbose_name, self.quebec_arrival_date],
            [self._meta.get_field("age").verbose_name, self.age],
            [self._meta.get_field("occupation").verbose_name, self.occupation],
            [self._meta.get_field("pronouns_preferred_name").verbose_name, self.pronouns_preferred_name],

            #### INFORMATIONS SUR LE CO-PARENT
            [self._meta.get_field("is_monoparental").verbose_name, self.is_monoparental],
            [self._meta.get_field("is_soloparental").verbose_name, self.is_soloparental],
            [self._meta.get_field("is_couple").verbose_name, self.is_couple],

            [self._meta.get_field("partner_full_name").verbose_name, self.partner_full_name],
            [self._meta.get_field("partner_email").verbose_name, self.partner_email],
            [self._meta.get_field("partner_occupation").verbose_name, self.partner_occupation],
            [self._meta.get_field("partner_absent_from_quebec").verbose_name, self.partner_absent_from_quebec],

            ##### PROGRAMME
            [self._meta.get_field("program").verbose_name, self.program],
        ]

    def __str__(self):
        return f"{self.profile_code} - {self.first_name} {self.last_name} ({self.email if self.email is not None else self.phone}) - {self.service_type}"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"


class ChildInfo(Orderable):
    """Model representing a child for some profiles (like Naissance)."""
    profile = ParentalKey("BaseServiceProfile", related_name="children", on_delete=models.CASCADE)

    # Fields for the child. You can add more fields (Age, etc.) here.
    info = models.CharField(max_length=255, verbose_name="Information enfant")

    panels = [
        FieldPanel("info"),
    ]
