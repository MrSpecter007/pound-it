from typing import Any, Final

from . import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile
from django.db import models


class Deuil(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO Replace placeholder fields after getting the complete form field list
    deceased_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nom de la personne décédée")
    deceased_date = models.DateField(null=True, blank=True , verbose_name="Date du décès")
    additional_notes = models.TextField(null=True, blank=True,
                                        verbose_name="Notes supplémentaires")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.DEUIL

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(6)

    @property
    def fields_needed_for_agent(self):
        general_fields: list[list[str | Any]] = super().fields_needed_for_agent
        # TODO Add fields needed for PDF generation
        return general_fields + [
            [self._meta.get_field("deceased_name").verbose_name, self.deceased_name],
            [self._meta.get_field("deceased_date").verbose_name, self.deceased_date],
        ]

    class Meta:
        verbose_name = "Profil Deuil"
        verbose_name_plural = "Profils Deuil"
