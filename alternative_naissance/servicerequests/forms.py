from django import forms
from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest

        fields = ['first_name', 'last_name','email', 'service_type']

        labels = {
            'first_name': 'Prenom',
            'last_name': 'Nom',
            'email': 'L\'address Courriel',
            'service_type': 'Type de service',
        }

class RejectRequestForm(forms.Form):
    reason = forms.CharField(label='Raison du refus', max_length=255)

class ShareForm(forms.Form):
    email = forms.EmailField(label='Email of the agent to share with')