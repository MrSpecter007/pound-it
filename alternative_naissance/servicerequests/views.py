from django.shortcuts import render, redirect, get_object_or_404

from .forms import ServiceRequestForm, ShareForm
from django.views.generic import TemplateView
from .models import Profile


# TODO create the user facing page for service request and complete the POST process
# def create_service_request(request):
#     if request.method == "POST":
#         form = ServiceRequestForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('success_page')
#     else:
#         form = ServiceRequestForm()
#     return render(request, 'servicerequests/service_request_form.html', {'form': form})



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
