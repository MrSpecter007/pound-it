from django.db import models
from wagtail.admin.panels import FieldPanel


class ServiceRequest(models.Model):
    SERVICE_CHOICES = [
        # TODO change this
        ("service1", "Service 1"),
        ("service2", "Service 2"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    # TODO make service request standalone and not as a snippet
    panels = [
        FieldPanel("name"),
        FieldPanel("email"),
        FieldPanel("service_type"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"


class Profile(models.Model):
    STATUS_CHOICES = [
        ("incomplete", "Incomplete"),
        ("complete", "Complete"),
    ]
    # TODO make profile copy the data of service request instead of one-to-one relation
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")

    panels = [
        FieldPanel("service_request"),
        FieldPanel("status"),
    ]

    def __str__(self):
        return self.service_request.name

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"