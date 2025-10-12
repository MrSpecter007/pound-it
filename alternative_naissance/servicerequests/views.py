from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from wagtail.admin.auth import user_passes_test

from .forms import ServiceRequestForm, ShareForm, RejectRequestForm
from .models import Profile, ServiceRequest
from .security import can_modify_servicerequests
from .utils import generate_profile_pdf, send_profile_email_to_agent


# TODO create the user facing page for service request and complete the POST process
def create_service_request(request: WSGIRequest) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_service_request_success')

    form = ServiceRequestForm()
    return render(request, 'servicerequests/service_request_form.html', {'form': form})


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
        profile = Profile(
            first_name=service_request.first_name,
            last_name=service_request.last_name,
            email=service_request.email,
            service_type=service_request.service_type,
        )
        profile.save()
        service_request.delete()
        return redirect('/admin/snippets/servicerequests/servicerequest/')

    return render(request,
                  'servicerequests/admin/accept_servicerequest.html',
                  {'service_request': service_request})


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
