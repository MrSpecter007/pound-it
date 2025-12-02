from typing import Any

from .base_service_profile import BaseServiceProfile
from django.db import models

from .shared_properties import ProfileCodePrefix


class Naissance(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO Replace the placeholder fields after getting the complete form field list
    birth_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nom de la personne naissante")

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
        return general_fields + [
            [self._meta.get_field("birth_name").verbose_name, self.birth_name],
        ]

    class Meta:
        verbose_name = "Profil Naissance"
        verbose_name_plural = "Profils Naissance"
