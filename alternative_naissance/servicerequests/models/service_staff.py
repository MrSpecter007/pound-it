from django.db import models
from wagtail.snippets.models import register_snippet


@register_snippet
class ServiceStaff(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Nom complet")
    extra_info = models.TextField(null=True, blank=True, verbose_name="Info supplémentaire")
    is_accompagnant = models.BooleanField(default=False, verbose_name="Accompagnante.e?")
    is_intervenant = models.BooleanField(default=False, verbose_name="Intervenante.e?")


    def __str__(self):
        return self.full_name

    @staticmethod
    def get_accompagnant_service_staff_names():
        """Returns a list of full names of all service staff members that are accompagnant. Used in the ACCOMPAGNANT.E and INTERVENANT.E using DatalistInput widget."""
        return list(ServiceStaff.objects.filter(is_accompagnant=True).values_list("full_name", flat=True))

    @staticmethod
    def get_intervenant_service_staff_names():
        """Returns a list of full names of all service staff members that are intervenant. Used in the INTERVENANT.E using DatalistInput widget."""
        return list(ServiceStaff.objects.filter(is_intervenant=True).values_list("full_name", flat=True))

    class Meta:
        verbose_name = "Accompagante.e / Intervenante.e"
        verbose_name_plural = "Accompagnantes.es / Intervenantes.es"
