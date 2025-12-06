from typing import Any

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from . import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile, ChildInfo


class InterventionPerinatale(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    number_of_pregnancies = models.IntegerField(null=True, blank=True,
                                                verbose_name="Nombre de grossesses incluant celle-ci",
                                                validators=[MinValueValidator(1), MaxValueValidator(10)])
    number_of_children = models.IntegerField(null=True, blank=True,
                                             verbose_name="Nombre d'enfants",
                                             validators=[MinValueValidator(1), MaxValueValidator(10)])
    # Add options later
    beginning_of_follow_up = models.TextField(null=True, blank=True,
                                              verbose_name="Début du suivi en intervention périnatale")

    referred_by = models.CharField(max_length=255, null=True, blank=True,
                                   verbose_name="Référé par")

    anticipated_new_born_delivery_date = models.DateField(null=True, blank=True,
                                                          verbose_name="Date prévue d'accouchement du/des nouveau/x-né/s")
    birth_date = models.DateField(null=True, blank=True,
                                  verbose_name="Date de naissance du/des nouveau/x-né/s")

    date_or_expected_date_of_event = models.DateField(null=True, blank=True,
                                                      verbose_name="Date de l'évènement ou Date prévue de l'événement (Deuil ou IG)")
    birth_place = models.CharField(max_length=255, null=True, blank=True,
                                   verbose_name="Lieu d'accouchement")
    follow_up_by = models.TextField(max_length=255, null=True, blank=True, verbose_name="Suivi effectué par")
    expected_people_at_childbirth = models.CharField(max_length=255, null=True, blank=True,
                                                     verbose_name="Personnes prévues à l'accouchement")
    special_conditions = models.TextField(null=True, blank=True,
                                          verbose_name="Conditions particulières reliées à cette grossesse")
    pregnancy_related_concerns = models.TextField(null=True, blank=True,
                                                  verbose_name="Inquiétudes reliées à la grossesse, accouchement ou postnatal")
    service_expectations = models.TextField(null=True, blank=True,
                                            verbose_name="Attentes reliées au service d'intervention périnatale")
    postnatal_needs = models.TextField(null=True, blank=True,
                                       verbose_name="Besoins ressources et/ou matériels en postnatale")
    community_resources = models.TextField(null=True, blank=True,
                                           verbose_name="Ressources et services communautaires présent auprès de la famille")
    support_network = models.TextField(null=True, blank=True,
                                       verbose_name="Réseau de soutien autour de la famille (amis, familles etc…)")

    ####### INTERVENANT.E PRINCIPAL.E
    principle_intervenant_person = models.CharField(max_length=255, null=True, blank=True,
                                                    verbose_name="Nom de Intervenant.e")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.INTERVENTION_PERINATALE

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        general_fields: list[list[str | Any]] = super().fields_needed_for_agent
        return (general_fields +
                # INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S aux formulaires
                [
                    [self._meta.get_field("number_of_pregnancies").verbose_name, self.number_of_pregnancies],
                    [self._meta.get_field("number_of_children").verbose_name,
                     self.number_of_children]
                ] +
                [  # Get all the childinfo objects and append them to the list
                    ["Info l'enfant #" + str(i), child.info] for (i, child) in
                    enumerate(ChildInfo.objects.filter(profile=self))]
                + [
                    [self._meta.get_field("beginning_of_follow_up").verbose_name, self.beginning_of_follow_up],
                    [self._meta.get_field("referred_by").verbose_name, self.referred_by],
                    [self._meta.get_field("anticipated_new_born_delivery_date").verbose_name,
                     self.anticipated_new_born_delivery_date],
                    [self._meta.get_field("birth_date").verbose_name, self.birth_date],
                    [self._meta.get_field("date_or_expected_date_of_event").verbose_name,
                     self.date_or_expected_date_of_event],
                    [self._meta.get_field("birth_place").verbose_name, self.birth_place],
                    [self._meta.get_field("follow_up_by").verbose_name, self.follow_up_by],
                    [self._meta.get_field("expected_people_at_childbirth").verbose_name,
                     self.expected_people_at_childbirth],
                    [self._meta.get_field("special_conditions").verbose_name, self.special_conditions],
                    [self._meta.get_field("pregnancy_related_concerns").verbose_name,
                     self.pregnancy_related_concerns],
                    [self._meta.get_field("service_expectations").verbose_name, self.service_expectations],
                    [self._meta.get_field("postnatal_needs").verbose_name, self.postnatal_needs],
                    [self._meta.get_field("community_resources").verbose_name, self.community_resources],
                    [self._meta.get_field("support_network").verbose_name, self.support_network],
                    ###### INTERVENANT.E PRINCIPAL.E'
                    [self._meta.get_field("principle_intervenant_person").verbose_name,
                     self.principle_intervenant_person],
                ]
                )

    class Meta:
        verbose_name = "Profil Intervention Périnatal"
        verbose_name_plural = "Profils Intervention Périnatal"
