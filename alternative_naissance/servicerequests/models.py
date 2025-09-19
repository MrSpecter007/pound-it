from django.db import models


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

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_type}"

    class Meta:
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"


class Profile(models.Model):

    SERVICE_CHOICES = [
        # TODO change this
        ("service1", "Service 1"),
        ("service2", "Service 2"),
    ]

    STATUS_CHOICES = [
        ("incomplete", "Incomplete"),
        ("complete", "Complete"),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES)

    age = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    immigration_status = models.CharField(max_length=255, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")



    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_type}"

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"