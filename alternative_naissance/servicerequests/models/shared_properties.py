# Setting it as private global variable as it is used by both classes
_SERVICE_CHOICES = [
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
