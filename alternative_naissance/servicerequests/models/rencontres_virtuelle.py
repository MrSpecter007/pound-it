from typing import Any

from django.db import models

from . import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile

class RencontresVirtuelles(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO
    rencontre_virtuelle_note = models.CharField(max_length=255, null=True, blank=True, verbose_name="Rencontre Virtuelle Notes")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.RENCONTRES_VIRTUELLES

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(6)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        # TODO
        return super().fields_needed_for_agent

    class Meta:
        verbose_name = "Profil Rencontre Virtuelle"
        verbose_name_plural = "Profils Rencontres Individuelles Virtuelles"
