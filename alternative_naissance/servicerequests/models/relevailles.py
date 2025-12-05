from typing import Any

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from servicerequests.models import BaseServiceProfile, ProfileCodePrefix
from servicerequests.models.base_service_profile import ChildInfo


class Relevailles(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)
    # TODO
    number_of_pregnancies = models.IntegerField(null=True, blank=True,
                                                verbose_name="Nombre de grossesses incluant celle-ci",
                                                validators=[MinValueValidator(1), MaxValueValidator(10)])
    number_of_children = models.IntegerField(null=True, blank=True, verbose_name="Nombre d’enfants",
                                             validators=[MinValueValidator(1), MaxValueValidator(10)])
    child_care_provider = models.CharField(max_length=255, null=True, blank=True, verbose_name="Milieu de garde")
    new_born_delivery_date = models.DateField(null=True, blank=True,
                                              verbose_name="Date de naissance du/des nouveau/x-né/s ")
    pregnancy_and_child_birth_progress = models.TextField(null=True, blank=True,
                                                          verbose_name="Déroulement de la grossesse et de l’accouchement")
    place_of_delivery = models.CharField(max_length=255, null=True, blank=True, verbose_name="Lieu d'accouchement")
    breastfeeding = models.TextField(null=True, blank=True, verbose_name="Allaitement")
    referred_by = models.CharField(max_length=255, null=True, blank=True, verbose_name="Référé par")
    postnatal_condition = models.TextField(null=True, blank=True,
                                           verbose_name="Conditions particulières reliées au postnatal")
    service_expectations = models.TextField(null=True, blank=True,
                                            verbose_name="Attentes reliées au service d'accompagnement")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.RELEVAILLES

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        # TODO
        general_fields: list[list[str | Any]] = super().fields_needed_for_agent
        return (general_fields +
                [
                    [self._meta.get_field("number_of_pregnancies").verbose_name, self.number_of_pregnancies],
                    [self._meta.get_field("number_of_children").verbose_name, self.number_of_children]
                ] +
                [  # Get all the childinfo objects and append them to the list
                    ["Info l'enfant #" + str(i), child.info] for (i, child) in
                    enumerate(ChildInfo.objects.filter(profile=self))
                ] +
                [
                    [self._meta.get_field("child_care_provider").verbose_name, self.child_care_provider],
                    [self._meta.get_field("new_born_delivery_date").verbose_name, self.new_born_delivery_date],
                    [self._meta.get_field("pregnancy_and_child_birth_progress").verbose_name,
                     self.pregnancy_and_child_birth_progress],
                    [self._meta.get_field("place_of_delivery").verbose_name, self.place_of_delivery],
                    [self._meta.get_field("breastfeeding").verbose_name, self.breastfeeding],
                    [self._meta.get_field("referred_by").verbose_name, self.referred_by],
                    [self._meta.get_field("postnatal_condition").verbose_name, self.postnatal_condition],
                    [self._meta.get_field("service_expectations").verbose_name, self.service_expectations]
                ]

                )

    class Meta:
        verbose_name = "Profil Relevailles"
        verbose_name_plural = "Profils Relevailles"
