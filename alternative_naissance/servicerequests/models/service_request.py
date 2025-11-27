from typing import Optional

from django.db import models
from .shared_properties import _SERVICE_CHOICES, _LANGUAGE_CHOICES, _CITIZENSHIP_STATUS_CHOICES


class ServiceRequest(models.Model):
    SERVICE_CHOICES = _SERVICE_CHOICES
    LANGUAGE_CHOICES = _LANGUAGE_CHOICES
    CITIZENSHIP_STATUS_CHOICES = _CITIZENSHIP_STATUS_CHOICES
    STATUS_CHOICES = [
        ("pending", "En attente"),
        # ("accepted", "Accepted"),
        ("rejected", "Réfusé"),
    ]

    # Basic information
    first_name = models.CharField(max_length=255, verbose_name="Prénom")
    last_name = models.CharField(max_length=255, verbose_name="Nom")

    # Service type and conditional fields
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES,
                                    verbose_name="Quel service voulez-vous recevoir?")

    # Conditional fields based on service type
    expected_delivery_date = models.DateField(null=True, blank=True,
                                              verbose_name="Quelle est votre date prévue d'accouchement?")
    child_birth_date = models.DateField(null=True, blank=True,
                                        verbose_name="Quelle est la date de naissance de votre ou vos enfants?")

    # Address fields
    street_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ville")
    province = models.CharField(max_length=100, null=True, blank=True, verbose_name="Province")
    postal_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="Code postal")
    no_permanent_address = models.BooleanField(default=False, verbose_name="Je n'ai pas d'adresse permanente")

    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone principal")
    no_phone = models.BooleanField(default=False, verbose_name="Je n'ai pas de téléphone")

    email = models.EmailField(blank=True, null=True, verbose_name="Courriel")
    no_email = models.BooleanField(default=False, verbose_name="Je n'ai pas de courriel")

    # Languages spoken (stored as comma-separated values)
    languages = models.CharField(max_length=255, verbose_name="Langue(s) parlée(s)")

    # Citizenship status
    citizenship_status = models.CharField(max_length=100, choices=CITIZENSHIP_STATUS_CHOICES,
                                          verbose_name="Statut de citoyenneté")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)

    refusal_reason = models.TextField(null=True, blank=True, verbose_name="Raison du refus")
    refusal_date = models.DateTimeField(null=True, blank=True, verbose_name="Date du refus")

    @property
    def service_full_name(self) -> str:
        """Used to get the more human-readable name of the service type."""
        return dict(self.SERVICE_CHOICES).get(self.service_type, self.service_type)

    service_full_name.fget.short_description = "Nom du service"  # Will be used by Wagtail snippet listing view (equivalent to verbose_name)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_full_name}"

    class Meta:
        verbose_name = "Demande de Service"
        verbose_name_plural = "Demandes de Service"
