import io
import datetime
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from servicerequests.models import Profile

def generate_profile_pdf(profile: Profile) -> io.BytesIO:
    """
    Generate a PDF file containing selected profile information.
    
    Args:
        profile: A Profile model instance
        
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
    data = [
        [profile._meta.get_field("first_name").verbose_name, profile.first_name],
        [profile._meta.get_field("last_name").verbose_name, profile.last_name],
        [profile._meta.get_field("service_type").verbose_name, dict(profile.SERVICE_CHOICES).get(profile.service_type, profile.service_type)]
    ]


    table = Table(data, colWidths=[150, 350])
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


def send_profile_email_to_agent(agent_email: str, profile: Profile, pdf_buffer: io.BytesIO) -> bool:
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
