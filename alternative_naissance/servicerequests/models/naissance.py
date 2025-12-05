from typing import Any

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .base_service_profile import BaseServiceProfile, ChildInfo
from .shared_properties import ProfileCodePrefix


class Naissance(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    number_of_pregnancies = models.IntegerField(null=True, blank=True,
                                                verbose_name="Nombre de grossesses incluant celle-ci",
                                                validators=[MinValueValidator(1), MaxValueValidator(10)])
    number_of_children = models.IntegerField(null=True, blank=True, verbose_name="Nombre d’enfants",
                                             validators=[MinValueValidator(1), MaxValueValidator(10)])
    anticipated_new_born_delivery_date = models.DateField(null=True, blank=True,
                                                          verbose_name="Date prévue d’accouchement du/des nouveau/x-né/s ")
    place_of_delivery = models.CharField(max_length=255, null=True, blank=True, verbose_name="Lieu d'accouchement")
    follow_up_by = models.CharField(max_length=255, null=True, blank=True, verbose_name="Suivi effectué par")
    referred_by = models.CharField(max_length=255, null=True, blank=True, verbose_name="Référé par")
    expected_people_at_childbirth = models.CharField(max_length=255, null=True, blank=True,
                                                     verbose_name="Personnes prévues à l'accouchement")
    comments_on_childbirth = models.TextField(null=True, blank=True,
                                              verbose_name="Commentaires sur les présences à l'accouchement")
    service_expectations = models.TextField(null=True, blank=True,
                                            verbose_name="Attentes reliées au service d'accompagnement")
    pregnancy_conditions = models.TextField(null=True, blank=True,
                                            verbose_name="Conditions particulières reliées à cette grossesse")

    pregnancy_concerns = models.TextField(null=True, blank=True, verbose_name="Inquiétudes reliées à la grossesse")

    birth_concerns = models.TextField(null=True, blank=True, verbose_name="Inquiétudes reliées à l'accouchement")

    baby_arrival_concerns = models.TextField(null=True, blank=True,
                                             verbose_name="Inquiétudes reliées à l'arrivée du/des bébé/s")

    has_prenatal_classes = models.BooleanField(null=True, blank=True, verbose_name="Cours prénataux")

    prenatal_classes_notes = models.TextField(null=True, blank=True, verbose_name="Notes sur les cours prénataux")


    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.NAISSANCE


    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)


    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        general_fields: list[list[str | Any]] = super().fields_needed_for_agent
        # TODO Define add the field needed for PDF generation
        return (general_fields +
                # INFORMATIONS SUR LA/LES GROSSESSE/S ET LE/LES ACCOUCHEMENT.S aux formulaires
                [
                    [self._meta.get_field("number_of_pregnancies").verbose_name, self.number_of_pregnancies],
                    [self._meta.get_field("number_of_children").verbose_name, self.number_of_children]
                ] +
                [  # Get all the childinfo objects and append them to the list
                    ["Info l'enfant #" + str(i), child.info] for (i, child) in
                    enumerate(ChildInfo.objects.filter(profile=self))]
                +
                [

                    [self._meta.get_field("anticipated_new_born_delivery_date").verbose_name,
                     self.anticipated_new_born_delivery_date],
                    [self._meta.get_field("place_of_delivery").verbose_name, self.place_of_delivery],
                    [self._meta.get_field("follow_up_by").verbose_name, self.follow_up_by],
                    [self._meta.get_field("referred_by").verbose_name, self.referred_by],
                    [self._meta.get_field("expected_people_at_childbirth").verbose_name, self.expected_people_at_childbirth],
                    [self._meta.get_field("comments_on_childbirth").verbose_name, self.comments_on_childbirth],
                    [self._meta.get_field("service_expectations").verbose_name, self.service_expectations],
                    [self._meta.get_field("pregnancy_conditions").verbose_name, self.pregnancy_conditions],
                    [self._meta.get_field("pregnancy_concerns").verbose_name, self.pregnancy_concerns],
                    [self._meta.get_field("birth_concerns").verbose_name, self.birth_concerns],
                    [self._meta.get_field("baby_arrival_concerns").verbose_name, self.baby_arrival_concerns],
                    [self._meta.get_field("has_prenatal_classes").verbose_name, self.has_prenatal_classes],
                    [self._meta.get_field("prenatal_classes_notes").verbose_name, self.prenatal_classes_notes],
                ]
                ##
                )


    class Meta:
        verbose_name = "Profil Naissance"
        verbose_name_plural = "Profils Naissance"
