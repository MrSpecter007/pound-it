from typing import Dict, Any

from django.db import models
from django.template import Template, Context


class EmailTemplate(models.Model):
    """
    Model for storing email templates that can be edited by admins.
    Each template is associated with a specific scenario (e.g., "user_request_submitted").
    """
    scenario = models.SlugField(
        max_length=100, 
        unique=True,
        verbose_name="Scénario",
        help_text="Identifiant unique pour ce modèle du courriel (ne pas modifier)"
    )
    scenario_description = models.TextField(
        max_length=255,
        blank=True,
        verbose_name="Description du scénario"
    )
    available_variables = models.TextField(
        blank=True,
        verbose_name="Variables disponibles",
        help_text="Liste des variables qui peuvent être utilisées dans le contenu de l'email"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du courriel",
        help_text="Sujet du courriel qui sera envoyé"
    )
    content = models.TextField(
        verbose_name="Contenu du courriel",
        help_text="Corps du courriel. Vous pouvez utiliser les variables listées ci-dessous."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modèle du courriel"
        verbose_name_plural = "Modèles du courriel"
        ordering = ["scenario"]

    def __str__(self) -> str:
        return f"{self.scenario}"
    
    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Render the email template with the given context.
        
        Args:
            context: Dictionary containing variables to be rendered in the template
            
        Returns:
            Dictionary with rendered title and content to be used in sending email
        """

        # Using Django templates to render the title and content with the variables
        title_template = Template(self.title)
        content_template = Template(self.content)
        
        template_context = Context(context)
        
        rendered_title = title_template.render(template_context)
        rendered_content = content_template.render(template_context)
        
        return {
            "title": rendered_title,
            "content": rendered_content
        }