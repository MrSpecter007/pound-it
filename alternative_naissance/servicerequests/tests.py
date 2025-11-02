from typing import override
from unittest.mock import patch, MagicMock

from wagtail.test.utils import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group

from servicerequests.models import ServiceRequest, BaseServiceProfile, Deuil
from servicerequests.utils import generate_profile_pdf


class ServiceRequestTests(TestCase):
    """
    Things need to be tested:
    - Receive service requests
    - Accepted service requests become profiles with correct fields initialized
    - Rejected service requests are deleted, and statistics are updated (TODO implement statistics)
    - Profile PDF generation
    - Profile PDF email sending to the correct recipient
    """

    @override
    def setUp(self):
        # Create a sample service request, profile and users for each test
        self.test_service_request = ServiceRequest.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            service_type="accompagnement_a_la_naissance",
            expected_delivery_date="2026-06-15",
            street_address="1234 Rue St",
            city="Montreal",
            province="Quebec",
            postal_code="B1B 1B1",
            phone="514-000-0000",
            languages="francais,anglais",
            citizenship_status="autre",
            no_permanent_address=False,
            no_phone=False,
            no_email=False,
            status="pending"
        )

        # Create a sample profile for PDF and email tests
        self.test_profile = Deuil.objects.create(
            first_name="Sam",
            last_name="Simpson",
            email="sam@example.com",
            service_type="accompagnement_au_deuil_perinatal",
            languages="anglais",
            citizenship_status="autre",
            no_permanent_address=True,
            no_phone=True,
            no_email=False,
            deceased_name="John Doe",
            deceased_date="2023-01-01",
            additional_notes="Test notes"
        )
        self.admin_user = User.objects.create_superuser("admin", "admin@test.test", "admin")
        self.staff_user = User.objects.create_user("staff", "staff@test.test", "staff")
        self.guest_user = User.objects.create_user("guest", "guest@test.test", "guest")
        Group.objects.get(name="Editors").user_set.add(self.staff_user)

    def test_create_service_request(self):
        """
        Test that a service request can be created via the form and is stored in the database.
        """

        response = self.client.post(reverse('create_service_request'),
                                    {
                                        'first_name': 'Daisy',
                                        'last_name': 'Doe',
                                        'email': 'daisy@example.com',
                                        'service_type': 'accompagnement_a_la_naissance',
                                        'expected_delivery_date': '2026-01-01',
                                        'street_address': '123 Test St',
                                        'city': 'Montreal',
                                        'province': 'Quebec',
                                        'postal_code': 'A1A1A1',
                                        'languages_choices': ['anglais'],
                                        'citizenship_status': 'autre',
                                        'no_permanent_address': False,
                                        'no_phone': True,
                                        'no_email': False
                                    })

        self.assertEqual(ServiceRequest.objects.count(), 2)  # Including the one from setUp
        service_request = ServiceRequest.objects.get(email="daisy@example.com")
        self.assertEqual(service_request.first_name, "Daisy")
        self.assertEqual(service_request.last_name, "Doe")
        self.assertEqual(service_request.service_type, "accompagnement_a_la_naissance")
        self.assertEqual(response.status_code, 302)


    def test_admin_can_accept_service_request(self):
        """
        Test that accepting a service request creates a new profile and deletes the service request.
        """
        # Count existing profiles before accepting a new request
        initial_profile_count = BaseServiceProfile.objects.count()

        # Admin accepts the service request
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('accept_service_request', kwargs={'pk': self.test_service_request.pk})
        )

        self.assertRedirects(response, '/admin/snippets/servicerequests/servicerequest/')

        self.assertEqual(BaseServiceProfile.objects.count(), initial_profile_count + 1)

        # Check if the service request was deleted as it should be replaced by a profile
        with self.assertRaises(ServiceRequest.DoesNotExist):
            ServiceRequest.objects.get(pk=self.test_service_request.pk)

        # Check if profile was created with correct data
        profile = BaseServiceProfile.objects.get(email="jane@example.com")
        self.assertEqual(profile.first_name, "Jane")
        self.assertEqual(profile.last_name, "Smith")
        self.assertEqual(profile.service_type, "accompagnement_a_la_naissance")

    def test_non_admin_cannot_accept_service_request(self):
        """
        Test that non-admin users (whether staff or a public user) cannot accept a service request.
        """
        self.client.force_login(self.guest_user)
        response = self.client.post(
            reverse('accept_service_request', kwargs={'pk': self.test_service_request.pk})
        )
        self.assertEqual(response.status_code, 302) # Should get redirected instead of succeed

        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('accept_service_request', kwargs={'pk': self.test_service_request.pk})
        )
        self.assertEqual(response.status_code, 302) # same with a non admin staff member

    def test_reject_service_request(self):
        """
        Test that rejecting a service request deletes it from the database.
        """
        # Count existing service requests before removal
        initial_count = ServiceRequest.objects.count()

        # Admin rejects the service request
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('reject_service_request', kwargs={'pk': self.test_service_request.pk}),
            {'reason': 'Invalid request'}
        )

        # Check redirection
        self.assertRedirects(response, '/admin/snippets/servicerequests/servicerequest/')

        # Check if the service request was deleted
        self.assertEqual(ServiceRequest.objects.count(), initial_count - 1)
        with self.assertRaises(ServiceRequest.DoesNotExist):
            ServiceRequest.objects.get(pk=self.test_service_request.pk)

    def test_admin_can_preview_profile_pdf(self) -> None:
        """
        Test that a PDF can be generated and previewed for a profile.
        """

        self.client.force_login(self.admin_user)
        # Call the PDF preview endpoint
        response = self.client.get(
            reverse('preview_profile_pdf', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower(), 'sub_id': self.test_profile.sub_id})
        )

        # Check response is successful
        self.assertEqual(response.status_code, 200)
        expected_pdf = generate_profile_pdf(self.test_profile)

        self.assertEqual(response.getvalue(), expected_pdf.getvalue())

        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_non_admin_cannot_preview_profile_pdf(self) -> None:
        """
        Test that a non-admin user (whether staff or a public user) cannot preview a profile PDF.
        """

        self.client.force_login(self.guest_user)
        response = self.client.get(
            reverse('preview_profile_pdf', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower() ,'sub_id': self.test_profile.sub_id})
        )
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.staff_user)
        response = self.client.get(
            reverse('preview_profile_pdf', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower() ,'sub_id': self.test_profile.sub_id})
        )
        self.assertEqual(response.status_code, 302)



    @patch('servicerequests.views.send_profile_email_to_agent')
    def test_admin_share_profile_success(self, mock_send_profile_email_to_agent: MagicMock) -> None:
        """
        Test sharing a profile via email successfully.
        """
        # Set up the mock to indicate successful email sending
        mock_send_profile_email_to_agent.return_value = True

        agent_email = "agent@example.com"

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('share_profile', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower(), 'sub_id': self.test_profile.sub_id}),
            {'email': agent_email}
        )

        self.assertRedirects(response, '/admin/snippets/servicerequests/servicerequest/')

        mock_send_profile_email_to_agent.assert_called_once()

        # Verify email was sent to correct agent address
        args, _ = mock_send_profile_email_to_agent.call_args_list[0]
        self.assertEqual(args[0], agent_email)

    @patch('servicerequests.views.send_profile_email_to_agent')
    def test_non_admin_cannot_share_profile(self, mock_send_profile_email_to_agent: MagicMock) -> None:
        """
        Test that non-admin users (whether staff or a public user) cannot share a profile to an agent.
        """
        mock_send_profile_email_to_agent.return_value = True

        agent_email = "agent@example.com"

        self.client.force_login(self.guest_user)
        self.client.post(
            reverse('share_profile', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower(), 'sub_id': self.test_profile.sub_id}),
            {'email': agent_email}
        )
        self.assertEqual(mock_send_profile_email_to_agent.call_count, 0)

        self.client.force_login(self.staff_user)
        self.client.post(
            reverse('share_profile', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower(), 'sub_id': self.test_profile.sub_id}),
            {'email': agent_email}
        )
        self.assertEqual(mock_send_profile_email_to_agent.call_count, 0)


    @patch('servicerequests.views.send_profile_email_to_agent')
    def test_share_profile_failure(self, mock_send_profile_email_to_agent):
        """
        Test handling of failures when sharing a profile via email.
        """

        # Set up the mock to indicate failed email sending
        mock_send_profile_email_to_agent.return_value = False

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('share_profile', kwargs={'profile_cls_lc': self.test_profile.__class__.__name__.lower() ,'sub_id': self.test_profile.pk}),
            {'email': "agent@example.com"}
        )

        # Check that we stay on the same page (no redirect)
        self.assertEqual(response.status_code, 200)

        # Check that the error message is in the response
        messages = list(response.context['messages'])
        self.assertTrue(any("Échec" in str(message) for message in messages))