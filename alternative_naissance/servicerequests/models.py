from django.db import models

# Setting it as private global variable as it is used by both classes
_SERVICE_CHOICE = [
    ("accompagnement_a_la_naissance", "Accompagnement à la naissance"),
    ("accompagnement_aux_relevailles", "Accompagnement aux relevailles/postnatal"),
    ("accompagnement_au_deuil_perinatal", "Accompagnement au deuil périnatal"),
    ("accompagnement_a_interruption_grossesse", "Accompagnement à l'interruption de grossesse"),
    ("accompagnement_virtuel_perinatal", "Accompagnement virtuel périnatal"),
    ("intervention_perinatale", "Intervention périnatale"),
]

# Language choices for multiple selection
_LANGUAGE_CHOICES = [
    ("francais", "Français"),
    ("anglais", "Anglais"),
    ("espagnol", "Espagnol"),
    ("creole", "Créole"),
    ("arabe", "Arabe"),
    ("italien", "Italien"),
    ("portugais", "Portugais"),
    ("russe", "Russe"),
    ("ukrainien", "Ukrainien"),
    ("punjabi", "Punjabi"),
]

# Citizenship status choices
_CITIZENSHIP_STATUS_CHOICES = [
    ("citoyen_canadien", "Citoyen.ne canadien.ne"),
    ("demandeur_asile", "Demandeur.euse d'asile"),
    ("permis_travail", "Permis de travail"),
    ("refugie", "Réfugié.e"),
    ("resident_permanent", "Résident.e permanent"),
    ("resident_temporaire", "Résident.e temporaire"),
    ("sans_statut", "Sans statut"),
    ("visa_etudes", "Visa d'études"),
    ("visa_tourisme", "Visa tourisme"),
    ("autre", "Autre"),
    ("prefere_ne_pas_repondre", "Préfère ne pas répondre"),
]

class ServiceRequest(models.Model):
    SERVICE_CHOICES = _SERVICE_CHOICE
    LANGUAGE_CHOICES = _LANGUAGE_CHOICES
    CITIZENSHIP_STATUS_CHOICES = _CITIZENSHIP_STATUS_CHOICES
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    # Basic information
    first_name = models.CharField(max_length=255, verbose_name="Prénom")
    last_name = models.CharField(max_length=255, verbose_name="Nom")
    
    # Service type and conditional fields
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES, verbose_name="Quel service voulez-vous recevoir?")
    
    # Conditional fields based on service type
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name="Quelle est votre date prévue d'accouchement?")
    child_birth_date = models.DateField(null=True, blank=True, verbose_name="Quelle est la date de naissance de votre ou vos enfants?")
    
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
    citizenship_status = models.CharField(max_length=100, choices=CITIZENSHIP_STATUS_CHOICES, verbose_name="Statut de citoyenneté")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.service_type}"

    class Meta:
        verbose_name = "Demande de Service"
        verbose_name_plural = "Demandes de Service"


class Profile(models.Model):
    """The Profile model mirrors all the information in the ServiceRequest model, and adds additional fields."""
    SERVICE_CHOICES = _SERVICE_CHOICE
    LANGUAGE_CHOICES = _LANGUAGE_CHOICES
    CITIZENSHIP_STATUS_CHOICES = _CITIZENSHIP_STATUS_CHOICES

    STATUS_CHOICES = [
        ("incomplete", "Incomplete"),
        ("complete", "Complete"),
    ]

    # Basic information
    first_name = models.CharField(max_length=255, verbose_name="Prénom")
    last_name = models.CharField(max_length=255, verbose_name="Nom")

    # Service type and conditional fields
    service_type = models.CharField(max_length=255, choices=SERVICE_CHOICES,
                                    verbose_name="Type de Service")

    # Conditional fields based on service type
    expected_delivery_date = models.DateField(null=True, blank=True,
                                              verbose_name="Date prévue d'accouchement")
    child_birth_date = models.DateField(null=True, blank=True,
                                        verbose_name="Date de naissance")

    # Address fields
    street_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ville")
    province = models.CharField(max_length=100, null=True, blank=True, verbose_name="Province")
    postal_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="Code postal")
    no_permanent_address = models.BooleanField(default=False, verbose_name="Pas d'adresse permanente")

    # Contact information
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone principal")
    no_phone = models.BooleanField(default=False, verbose_name="Pas de téléphone")

    email = models.EmailField(blank=True, null=True, verbose_name="Courriel")
    no_email = models.BooleanField(default=False, verbose_name="Pas de courriel")

    # Languages spoken (stored as comma-separated values)
    languages = models.CharField(max_length=255, verbose_name="Langue(s) parlée(s)")

    # Citizenship status
    citizenship_status = models.CharField(max_length=100, choices=CITIZENSHIP_STATUS_CHOICES,
                                          verbose_name="Statut de citoyenneté")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email if self.email is not None else self.phone}) - {self.service_type}"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"