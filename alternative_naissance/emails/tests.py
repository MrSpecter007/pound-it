from django.test import TestCase
from django.core import mail

from .models import EmailTemplate
from .utils import send_templated_email
from .registry import register_email_template, get_declared_templates


class EmailTemplateModelTests(TestCase):
    """Tests for the EmailTemplate model."""
    
    def setUp(self) -> None:
        self.template = EmailTemplate.objects.create(
            scenario="test_scenario",
            title="Hello {{ user_first_name }}",
            content="Hello {{ user_first_name }} {{ user_last_name }},\n\nThis is a test email.",
            available_variables="{{ user_first_name }}, {{ user_last_name }}"
        )
    
    def test_str_representation(self) -> None:
        """Test the string representation of the model."""
        self.assertEqual(str(self.template), "test_scenario")
    
    def test_render_method(self) -> None:
        """Test the render method with a context."""
        context = {
            "user_first_name": "John",
            "user_last_name": "Doe"
        }
        
        rendered = self.template.render(context)
        
        self.assertEqual(rendered["title"], "Hello John")
        self.assertEqual(rendered["content"], "Hello John Doe,\n\nThis is a test email.")


class EmailRegistryTests(TestCase):
    def test_register_template(self) -> None:
        """Test registering a template."""
        # Clear any existing templates
        from emails.registry import _default_templates
        _default_templates.clear()
        
        # Register a template
        register_email_template(
            scenario="test_registry",
            title="Test Title",
            content="Test Content",
            available_variables="var1, var2"
        )
        
        # Get the templates
        templates = get_declared_templates()
        
        # Check that the template was registered
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["scenario"], "test_registry")
        self.assertEqual(templates[0]["title"], "Test Title")
        self.assertEqual(templates[0]["content"], "Test Content")
        self.assertEqual(templates[0]["available_variables"], "var1, var2")


class EmailSendingTests(TestCase):

    def setUp(self) -> None:
        self.template = EmailTemplate.objects.create(
            scenario="test_sending",
            title="Hello {{ user_first_name }}",
            content="Hello {{ user_first_name }} {{ user_last_name }},\n\nThis is a test email.",
            available_variables="{{ user_first_name }}, {{ user_last_name }}"
        )
        
        # Clear the test outbox
        mail.outbox = []
    
    def test_send_templated_email(self) -> None:
        """Test sending an email using a template."""
        context = {
            "user_first_name": "John",
            "user_last_name": "Doe"

        }
        
        result = send_templated_email(
            scenario="test_sending",
            context=context,
            to_emails=["test@example.com"]
        )
        
        # Check that the email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check the email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Hello John")
        self.assertEqual(email.body, "Hello John Doe,\n\nThis is a test email.")
        self.assertEqual(email.to, ["test@example.com"])
    
    def test_send_templated_email_nonexistent_template(self) -> None:
        """Test sending an email with a nonexistent template."""
        context = {"user_first_name": "John", "user_last_name": "Doe"}
        
        # Try to send the email with a nonexistent template
        result = send_templated_email(
            scenario="nonexistent_template",
            context=context,
            to_emails=["test@example.com"]
        )
        
        # Check that the email was not sent
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)