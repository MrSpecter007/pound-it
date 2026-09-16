import logging
from typing import Dict, Any, List, Optional

from django.core.mail import EmailMessage

from .models import EmailTemplate

logger = logging.getLogger(__name__)


def get_email_template(scenario: str) -> Optional[EmailTemplate]:
    """
    Get an email template by scenario.
    
    Args:
        scenario: The scenario identifier for the template
        
    Returns:
        EmailTemplate instance or None if not found
    """
    try:
        return EmailTemplate.objects.get(scenario=scenario)
    except EmailTemplate.DoesNotExist:
        logger.error(f"Email template for scenario '{scenario}' does not exist")
        return None


def send_templated_email(
        scenario: str,
        context: Dict[str, Any],
        to_emails: List[str],
        from_email: Optional[str] = None
) -> bool:
    """
    Send an email using a template.
    
    Args:
        scenario: The scenario identifier for the template
        context: Dictionary containing variables to be rendered in the template
        to_emails: List of recipient email addresses
        from_email: Sender email address (uses DEFAULT_FROM_EMAIL if not provided)
        reply_to: List of reply-to email addresses
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    # Get the template
    template = get_email_template(scenario)
    if not template:
        return False

    # Render the template with the context
    rendered = template.render(context)

    # Create the email message
    email = EmailMessage(
        subject=rendered["title"],
        body=rendered["content"],
        to=to_emails,
        from_email=from_email,
    )

    # Send the email
    try:
        email.send(fail_silently=False)
        # logger.info(f"Email sent successfully for scenario '{scenario}' to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Error sending email for scenario '{scenario}': {e}")
        return False
