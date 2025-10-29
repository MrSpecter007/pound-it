from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from wagtail.admin.auth import user_passes_test

from .forms import ServiceRequestForm, ShareForm, RejectRequestForm
from .models import Profile, ServiceRequest
from .security import can_modify_servicerequests
from .utils import generate_profile_pdf, send_profile_email_to_agent


def create_service_request(request: WSGIRequest) -> HttpResponseRedirect | HttpResponse:
    """
    Handles the creation of a new service request.
    Displays the form on GET requests and processes form data on POST requests.
    """
    if request.method == "POST":
        form: ServiceRequestForm = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request: ServiceRequest = form.save()
            # TODO: Send email to user and admin about service request creation
            return redirect('create_service_request_success')
    else:
        form: ServiceRequestForm = ServiceRequestForm()
        
    return render(
        request, 
        'servicerequests/service_request_form.html', 
        {'form': form}
    )


def create_service_request_success(request: WSGIRequest) -> HttpResponse:
    return render(request, 'servicerequests/service_request_form_submitted.html')


## Endpoints for Admin pages

@user_passes_test(can_modify_servicerequests)
def accept_service_request(request: WSGIRequest, pk: int) -> HttpResponseRedirect | HttpResponse:
    """
    Handles accepting a service request. Provides a page for admin to confirm or cancel the action.
    If confirmed, a profile entity is created based on the service request content, and the service request is deleted.
    """
    service_request: ServiceRequest = get_object_or_404(ServiceRequest, pk=pk)

    if request.method == 'POST':
        # Create a new Profile with all the fields from the ServiceRequest
        service_request_kwargs: dict = service_request.__dict__.copy() # Making a copy to avoid altering the original service_request
        # Remove not needed fields
        service_request_kwargs.pop('id')
        service_request_kwargs.pop('status')
        service_request_kwargs.pop('created_at')
        service_request_kwargs.pop('_state')

        profile: Profile = Profile(**service_request_kwargs)

        # Save the profile
        profile.save()

        # Add success message
        messages.success(
            request,
            f"La demande de service de {service_request.first_name} {service_request.last_name} a été acceptée avec succès."
        )

        # Delete the service request
        service_request.delete()
        
        return redirect('/admin/snippets/servicerequests/profile/')

    return render(
        request,
        'servicerequests/admin/accept_servicerequest.html',
        {'service_request': service_request}
    )


@user_passes_test(can_modify_servicerequests)
def reject_service_request(request: WSGIRequest, pk: int) -> HttpResponseRedirect | HttpResponse:
    """
    Handles rejecting a service request. Provides a page for admin to confirm with a Reason for Rejection, or cancel the action.
    If confirmed, the service request is deleted.
    """

    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.method == 'POST':
        service_request.delete()
        #TODO add statistic recording the rejected requests
        return redirect('/admin/snippets/servicerequests/servicerequest/')

    form = RejectRequestForm()
    return render(request,
                  'servicerequests/admin/reject_servicerequest.html',
                  {'service_request': service_request, 'form': form})



@user_passes_test(can_modify_servicerequests)
def preview_profile_pdf(request: WSGIRequest, pk: int) -> FileResponse:
    """
    Generates and serves a PDF preview of the profile.
    This allows admins to view the PDF before sending it to an agent.
    """
    profile = get_object_or_404(Profile, pk=pk)

    pdf_buffer = generate_profile_pdf(profile)

    return FileResponse(pdf_buffer, as_attachment=False, filename=f"preview_profile_{profile.first_name}_{profile.last_name}.pdf")


@user_passes_test(can_modify_servicerequests)
def share_profile(request: WSGIRequest, pk: int) -> HttpResponse | HttpResponseRedirect:
    """
    Handles sharing a Profile through a standalone page.
    Allows admin to input the agent info, and it will send the PDF version
    of the profile to the agent email.
    """
    profile = get_object_or_404(Profile, pk=pk)

    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            # Get the email from the form
            agent_email = form.cleaned_data['email']
            
            try:
                # Generate PDF
                pdf_buffer = generate_profile_pdf(profile)
                
                # Send email with PDF attachment
                email_sent = send_profile_email_to_agent(agent_email, profile, pdf_buffer)
                
                if email_sent:
                    messages.success(request, f"Profil partagé avec {agent_email}")
                    return redirect('/admin/snippets/servicerequests/profile/')
                else:
                    messages.error(request, f"Échec de 'envoi du courriel á {agent_email}. Veuillez réessayer.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
            
    else:
        form = ShareForm()

    return render(
        request,
        'servicerequests/admin/share_profile.html',
        {
            'profile': profile,
            'form': form,
        }
    )
