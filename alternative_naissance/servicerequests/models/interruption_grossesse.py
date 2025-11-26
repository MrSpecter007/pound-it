from typing import Any

from .shared_properties import ProfileCodePrefix
from .base_service_profile import BaseServiceProfile
from django.db import models

class InterruptionGrossesse(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO
    grossesse_note = models.CharField(max_length=255, null=True, blank=True, verbose_name="Interruption Grossesse Notes")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.INTERRUPTION_GROSSESSE

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(6)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        # TODO
        return super().fields_needed_for_agent

    class Meta:
        verbose_name = "Profil Interruption de Grossesse"
        verbose_name_plural = "Profils Interruption de Grossesse"
