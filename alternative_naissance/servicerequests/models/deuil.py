from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile, ChildInfo


class Deuil(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    number_of_pregnancies = models.IntegerField(null=True, blank=True,
                                                verbose_name="Nombre de grossesses incluant celle-ci",
                                                validators=[MinValueValidator(1), MaxValueValidator(10)])
    number_of_children_exclude_deceased = models.IntegerField(null=True, blank=True,
                                                              verbose_name="Nombre d’enfants (excluant celui lié au deuil)",
                                                              validators=[MinValueValidator(1), MaxValueValidator(10)])
    date_or_expected_date_of_event = models.DateField(null=True, blank=True,
                                                      verbose_name="Date de l’évènement ou Date prévue de l’événement")
    place = models.CharField(max_length=255, null=True, blank=True, verbose_name="Lieu")
    # gestational_age = models.CharField(max_length=255, null=True, blank=True, verbose_name="Âge gestationnel") # IG only
    # pregnancy_termination_method = models.CharField(max_length=255, null=True, blank=True, verbose_name="Méthod d'interruption de grossesse") # IG only
    event_description = models.TextField(null=True, blank=True, verbose_name="Description de l’évènement")
    special_condition = models.TextField(null=True, blank=True, verbose_name="Conditions particulières")
    service_expectations = models.TextField(null=True, blank=True,
                                            verbose_name="Attentes reliées au service (ex : écoute, répit, aide organisationnelle, recherche de ressources, conseils, démarches, soutien, démarches funéraires, création d'un rituel, méditation, apaisement par l'écriture, etc.) ")
    referred_by = models.CharField(max_length=255, null=True, blank=True, verbose_name="Référé par")

    ######## ACCOMPAGNANT.E PRINCIPAL.E
    principle_accompanying_person = models.CharField(max_length=255, null=True, blank=True,
                                                     verbose_name="Accompagnant.e principal.e")
    principle_status = models.CharField(max_length=255, null=True, blank=True,
                                        verbose_name="Statut de l'accompagnant.e principal.e")
    principle_trainee_paid_amount = models.IntegerField(null=True, blank=True,
                                                        verbose_name="Montant payé par stagiaire (Si applicable)")
    principle_balance_sheet_submission_date = models.DateField(null=True, blank=True,
                                                               verbose_name="Date de remise du bilan")
    principle_amount_paid = models.IntegerField(null=True, blank=True, verbose_name="Montant payé")
    principle_payment_method = models.CharField(max_length=255, null=True, blank=True,
                                                verbose_name="Méthod de paiement")

    ######## ACCOMPAGNANT.E SECONDAIRE
    secondary_accompanying_person = models.CharField(max_length=255, null=True, blank=True,
                                                     verbose_name="Accompagnant.e secondaire")
    secondary_status = models.CharField(max_length=255, null=True, blank=True,
                                        verbose_name="Statut de l'accompagnant.e secondaire")
    secondary_trainee_paid_amount = models.IntegerField(null=True, blank=True,
                                                        verbose_name="Montant payé par stagiaire (Si applicable)")
    secondary_balance_sheet_submission_date = models.DateField(null=True, blank=True,
                                                               verbose_name="Date de remise du bilan")
    secondary_amount_paid = models.IntegerField(null=True, blank=True, verbose_name="Montant payé")
    secondary_payment_method = models.CharField(max_length=255, null=True, blank=True,
                                                verbose_name="Méthod de paiement")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.DEUIL

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)

    @property
    def fields_needed_for_agent(self):
        general_fields: list[list[str | Any]] = super().fields_needed_for_agent
        # TODO Define add the field needed for PDF generation
        return (general_fields +
                # INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S aux formulaires
                [
                    [self._meta.get_field("number_of_pregnancies").verbose_name, self.number_of_pregnancies],
                    [self._meta.get_field("number_of_children_exclude_deceased").verbose_name,
                     self.number_of_children_exclude_deceased]
                ] +
                [  # Get all the childinfo objects and append them to the list
                    ["Info l'enfant #" + str(i), child.info] for (i, child) in
                    enumerate(ChildInfo.objects.filter(profile=self))]
                + [

                    [self._meta.get_field("date_or_expected_date_of_event").verbose_name,
                     self.date_or_expected_date_of_event],
                    [self._meta.get_field("place").verbose_name, self.place],
                    [self._meta.get_field("event_description").verbose_name, self.event_description],
                    [self._meta.get_field("special_condition").verbose_name, self.special_condition],
                    [self._meta.get_field("service_expectations").verbose_name, self.service_expectations],
                    [self._meta.get_field("referred_by").verbose_name, self.referred_by],
                    ######## ACCOMPAGNANT.E
                    [self._meta.get_field("principle_accompanying_person").verbose_name,
                     self.principle_accompanying_person],
                    [self._meta.get_field("secondary_accompanying_person").verbose_name,
                     self.secondary_accompanying_person]
                ]
                )

    class Meta:
        verbose_name = "Profil Deuil"
        verbose_name_plural = "Profils Deuil"
