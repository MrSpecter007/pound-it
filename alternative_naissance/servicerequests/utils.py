import io
import datetime
from typing import Dict, Any, Optional

from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from servicerequests.models import ServiceProfile, ServiceRequest


def generate_profile_pdf(service_profile: ServiceProfile) -> io.BytesIO:
    """
    Generate a PDF file containing selected profile information.
    
    Args:
        service_profile: A Profile model instance
        
    Returns:
        BytesIO object containing the PDF file
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Content for the PDF
    elements = []

    # Add title
    title = Paragraph("Profil pour l'agent", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Add profile information as a table
    data = service_profile.fields_needed_for_agent

    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Indicate profile generation date
    footer_text = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)

    doc.build(elements)

    # Reset the buffer position to the beginning
    buffer.seek(0)

    return buffer


def send_profile_email_to_agent(agent_email: str, profile: ServiceProfile, pdf_buffer: io.BytesIO) -> bool:
    """
    Send an email with the profile PDF as an attachment.
    
    Args:
        agent_email: Email address of the agent
        profile: Profile model instance
        pdf_buffer: BytesIO object containing the PDF file
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    subject = f"Profil de {profile.first_name} {profile.last_name} pour Alternative Naissance"
    message = f"""
    Salut,
    
    Veuillez vérifier le profil ci-join pour {profile.first_name} {profile.last_name}.
    
    Type de Service: {dict(profile.SERVICE_CHOICES).get(profile.service_type, profile.service_type)}
    
    
    Cordialement,
    Alternative Naissance
    
    [This is an automated message. Please do not reply to this email.]
    """

    email = EmailMessage(
        subject=subject,
        body=message,
        to=[agent_email],
    )

    # Attach the PDF
    email.attach(
        f"profile_{profile.first_name}_{profile.last_name}.pdf",
        pdf_buffer.read(),
        'application/pdf'
    )

    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_service_request_emails(service_request: ServiceRequest) -> Dict[str, bool]:
    """
    Send confirmation emails after user submits a new service request.
    
    Sends two emails:
    1. A confirmation email to the user who submitted the request
    2. A notification email to the admin
    
    Args:
        service_request: The ServiceRequest instance
        
    Returns:
        Dictionary with status of each email sent. Keys: "user_email_sent" and "admin_email_sent".
    """
    results = {
        "user_email_sent": False,
        "admin_email_sent": False
    }

    # Import here to avoid circular imports
    from emails.utils import send_templated_email
    try:
        # Prepare context for email templates
        # Get the display name for the service type
        service_type_display = dict(ServiceRequest.SERVICE_CHOICES).get(
            service_request.service_type,
            service_request.service_type
        )

        context = {
            "user_first_name": service_request.first_name,
            "user_last_name": service_request.last_name,
            "user_email": service_request.email,
            "service_type_display": service_type_display,
            "request_created_date": service_request.created_at.strftime("%Y-%m-%d")
        }

        # Send confirmation email to user if email exists (since user may use phone instead of email)
        if service_request.email is not None:
            results["user_email_sent"] = send_templated_email(
                scenario="service_request_confirmation",
                context=context,
                to_emails=[service_request.email]
            )
        else:
            print(f"No email provided for service request")

        # Send notification email to admin
        admin_email = getattr(settings, "ADMIN_EMAIL", None)
        if admin_email:
            results["admin_email_sent"] = send_templated_email(
                scenario="service_request_admin_notification",
                context=context,
                to_emails=[admin_email]
            )

    except ImportError as e:
        # The emails app might not be installed yet
        print(f"Error importing email util functions: {e}")
    except Exception as e:
        print(f"Error sending service request emails: {e}")

    return results
