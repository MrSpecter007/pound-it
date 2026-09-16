from django.apps import AppConfig
from typing import Any


class ServicerequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'servicerequests'

    def ready(self) -> None:
        """
        Register email templates when the app is ready.
        """
        # Import here to avoid circular imports
        from emails.registry import register_email_template

        # Register user-facing service request confirmation email template
        register_email_template(
            scenario="service_request_confirmation",
            title="Confirmation de votre demande de service - {{ service_type_display }}",
            content="""Bonjour {{ user_first_name }},

Nous avons bien reçu votre demande de service "{{ service_type_display }}".

Notre équipe va examiner votre demande dans les plus brefs délais et vous contactera bientôt.

Merci de votre confiance.

Cordialement,
L'équipe Alternative Naissance
""",
            available_variables="""
{{ user_first_name }} - Prénom du client | 

{{ user_last_name }} - Nom de famille du client | 

{{ user_email }} - Adresse courriel du client | 

{{ service_type_display }} - Type de service (nom affiché) | 

{{ request_created_date }} - Date de création de la demande | 
""",

            scenario_description="""
Le courriel qui sera envoyé à l'utilisateur lorsqu'il soumettra une demande.           
"""
        )

        # Register admin notification email template
        register_email_template(
            scenario="service_request_admin_notification",
            title="Nouvelle demande de service - {{ service_type_display }}",
            content="""Bonjour Admin,

Une nouvelle demande de service a été soumise:

Nom: {{ user_first_name }} {{ user_last_name }}

Email: {{ user_email }}

Type de service: {{ service_type_display }}

Date de soumission: {{ request_created_date }}

Veuillez vous connecter à l'interface d'administration pour examiner cette demande.

""",
            available_variables="""
{{ user_first_name }} - Prénom du client | 

{{ user_last_name }} - Nom de famille du client | 

{{ user_email }} - Adresse courriel du client | 

{{ service_type_display }} - Type de service (nom affiché) | 

{{ request_created_date }} - Date de création de la demande | 
""",

            scenario_description="""
Le courriel qui sera envoyé á l'administrateur lorsque l'utilisateur somettra une demande.
"""
        )
