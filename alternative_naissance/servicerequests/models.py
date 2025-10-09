from django.db import models

# TODO complete this
# Setting it as private global variable as it is used by both classes
_SERVICE_CHOICE =[
    ("accompagnement_a_la_naissance", "Accompagnement à la naissance"),
    ("soutien_postnatal_a_domicile", "Relevailles - soutien postnatal à domicile"),
]

class ServiceRequest(models.Model):
    SERVICE_CHOICES = _SERVICE_CHOICE
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    first_name = models.CharField(max_length=255, verbose_name="Prenom")
    last_name = models.CharField(max_length=255, verbose_name="Nom")
    email = models.EmailField(verbose_name="Courriel")
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES, verbose_name="Type de service")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_type}"

    class Meta:
        verbose_name = "Demande de Service"
        verbose_name_plural = "Demandes de Service"


class Profile(models.Model):

    SERVICE_CHOICES = _SERVICE_CHOICE

    STATUS_CHOICES = [
        ("incomplete", "Incomplete"),
        ("complete", "Complete"),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES)

    age = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    immigration_status = models.CharField(max_length=255, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")



    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_type}"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"