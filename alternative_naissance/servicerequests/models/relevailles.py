from typing import Any

from servicerequests.models import BaseServiceProfile, ProfileCodePrefix
from django.db import models

class Relevailles(BaseServiceProfile):
    sub_id = models.AutoField(primary_key=True)

    # TODO
    relevailles_note = models.CharField(max_length=255, null=True, blank=True, verbose_name="Relevailles Notes")

    @property
    def profile_code_prefix(self) -> ProfileCodePrefix:
        return ProfileCodePrefix.RELEVAILLES

    @property
    def profile_code(self) -> str:
        return self.profile_code_prefix.value + str(self.sub_id).zfill(7)

    @property
    def fields_needed_for_agent(self) -> list[list[str | Any]]:
        # TODO
        return super().fields_needed_for_agent

    class Meta:
        verbose_name = "Profil Relevailles"
        verbose_name_plural = "Profils Relevailles"