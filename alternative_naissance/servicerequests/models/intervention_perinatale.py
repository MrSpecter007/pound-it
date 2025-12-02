from typing import Any

from django.db import models

from . import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile

class InterventionPerinatale(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO
    intervention_perinatal_note = models.CharField(max_length=255, null=True, blank=True, verbose_name="Intervention Perinatal Notes")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.INTERVENTION_PERINATALE

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        # TODO
        return super().fields_needed_for_agent

    class Meta:
        verbose_name = "Profil Intervention Périnatal"
        verbose_name_plural = "Profils Intervention Périnatal"