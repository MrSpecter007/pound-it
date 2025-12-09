from django import forms
from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['name', 'email', 'service_type']


class ShareForm(forms.Form):
    email = forms.EmailField(label='Email of the agen to share with')