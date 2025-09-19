from django.shortcuts import render, redirect, get_object_or_404

from .forms import ServiceRequestForm, ShareForm, RejectRequestForm
from .models import Profile, ServiceRequest


# TODO create the user facing page for service request and complete the POST process
def create_service_request(request):
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_service_request_success')
    else:
        form = ServiceRequestForm()
    return render(request, 'servicerequests/service_request_form.html', {'form': form})


def create_service_request_success(request):
    return render(request, 'servicerequests/service_request_form_submitted.html')


## Endpoints for Admin pages

def accept_service_request(request, pk):
    """Handles accepting a service request. Provides a page for admin to confirm or cancel the action.
    If confirmed, a profile entity is created based on the service request content and the service request is deleted."""

    service_request = get_object_or_404(ServiceRequest, pk=pk)
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


def reject_service_request(request, pk):
    """Handles rejecting a service request. Provides a page for admin to confirm with a Reason for Rejection, or cancel the action.
    If confirmed, the service request is deleted."""

    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        service_request.delete()
        return redirect('/admin/snippets/servicerequests/servicerequest/')

    form = RejectRequestForm()
    return render(request,
                  'servicerequests/admin/reject_servicerequest.html',
                  {'service_request': service_request, 'form': form})


def share_profile(request, pk):
    """
    Handles sharing a Profile through a standalone page.
    Allows admin to input the agent info, and it will send the PDF version
    of the profile to the agent email.
    """
    profile = get_object_or_404(Profile, pk=pk)

    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            # TODO implement PDF conversion and email sending logic
            return redirect('success_page')

    form = ShareForm()

    return render(
        request,
        'servicerequests/admin/share_profile.html',
        {
            'profile': profile,
            'form': form,
        }
    )
