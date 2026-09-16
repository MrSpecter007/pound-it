import logging

from django.apps import AppConfig
from django.db import transaction, OperationalError, ProgrammingError
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class EmailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emails'

    def ready(self) -> None:
        # Import here to avoid circular imports
        from . import registry
        from .models import EmailTemplate

        @receiver(post_migrate)
        def create_default_email_templates(sender: AppConfig, **kwargs: dict) -> None:
            """
            Create default email templates after migrations are applied.
            
            This ensures that templates declared by other apps are created in the database.
            Only creates templates that don't already exist (based on scenario).
            """
            # Only process for this app to avoid running multiple times
            if sender.name != self.name:
                return

            logger.info("Creating default email templates...")

            # Get all declared templates from the registry
            for template_declaration in registry.get_declared_templates():
                try:
                    with transaction.atomic():
                        template, created = EmailTemplate.objects.get_or_create(
                            scenario=template_declaration["scenario"],
                            defaults={
                                "title": template_declaration["title"],
                                "content": template_declaration["content"],
                                "available_variables": template_declaration["available_variables"],
                                "scenario_description": template_declaration["scenario_description"]
                            }
                        )

                        if created:
                            logger.info(f"Created email template for scenario: {template.scenario}")

                except (OperationalError, ProgrammingError) as e:
                    # The table might not exist in some contexts; ignore safe failures
                    logger.warning(f"Could not create email template: {e}")
                    pass