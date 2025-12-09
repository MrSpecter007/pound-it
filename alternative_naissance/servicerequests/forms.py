from django import forms
from django.core.exceptions import ValidationError
from typing import Dict, Any, List
from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    """
    The public facing form for requesting a service.
    """
    # Create MultipleChoiceField for languages, will be stored as comma separated strings in db
    languages_choices: forms.MultipleChoiceField = forms.MultipleChoiceField(
        choices=ServiceRequest.LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Langue(s) parlée(s)"
    )
    other_language: forms.CharField = forms.CharField(
        max_length=255,
        required=False,
        label="Autre langue"
    )
    
    class Meta:
        model = ServiceRequest
        fields = [
            'service_type', 
            'expected_delivery_date', 
            'child_birth_date',
            'first_name', 
            'last_name',
            'street_address', 
            'city', 
            'province', 
            'postal_code', 
            'no_permanent_address',
            'phone', 
            'no_phone',
            'email', 
            'no_email',
            'languages_choices',
            'other_language',
            'citizenship_status'
        ]
        
        widgets: Dict[str, forms.Widget] = {
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'child_birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
        

    def clean(self) -> Dict[str, Any]:
        cleaned_data: Dict[str, Any] = super().clean()
        
        # Validate that user can't select both "no phone" and "no email"
        no_phone: bool = cleaned_data.get('no_phone', False)
        no_email: bool = cleaned_data.get('no_email', False)
        
        if no_phone and no_email:
            raise ValidationError(
                "Vous devez fournir au moins un moyen de contact (téléphone ou courriel)."
            )
            
        # Validate address fields if no_permanent_address is not checked
        no_permanent_address: bool = cleaned_data.get('no_permanent_address', False)
        if not no_permanent_address:
            required_address_fields: List[str] = ['street_address', 'city', 'province', 'postal_code']
            for field in required_address_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est obligatoire.")
                    
        # Validate phone if no_phone is not checked
        if not no_phone and not cleaned_data.get('phone'):
            self.add_error('phone', "Ce champ est obligatoire si vous avez un téléphone.")
            
        # Validate email if no_email is not checked
        if not no_email and not cleaned_data.get('email'):
            self.add_error('email', "Ce champ est obligatoire si vous avez un courriel.")
            
        # Validate conditional fields based on service type
        service_type: str = cleaned_data.get('service_type', '')
        
        if service_type == 'accompagnement_a_la_naissance' and not cleaned_data.get('expected_delivery_date'):
            self.add_error('expected_delivery_date', "Ce champ est obligatoire pour ce type de service.")
            
        if service_type == 'accompagnement_aux_relevailles' and not cleaned_data.get('child_birth_date'):
            self.add_error('child_birth_date', "Ce champ est obligatoire pour ce type de service.")
            
        # Process languages_choices into comma-separated string
        languages_choices: List[str] = cleaned_data.get('languages_choices', [])
        other_language: str = cleaned_data.get('other_language', '')
        if other_language and other_language is not "":
            if not other_language.isalpha():
               self.add_error('other_language', "Ce champ doit contenir uniquement des lettres.")
            languages_choices.append(other_language)

        if len(languages_choices) == 0:
            self.add_error('languages_choices', 'Ce champ est obligatoire')

        cleaned_data['languages'] = ','.join(languages_choices)
            
        return cleaned_data
        
    def save(self, commit: bool = True) -> ServiceRequest:
        instance: ServiceRequest = super().save(commit=False)
        
        # Save languages as comma-separated string
        languages_choices: List[str] = self.cleaned_data.get('languages_choices', [])
        if languages_choices:
            instance.languages = ','.join(languages_choices)
            
        if commit:
            instance.save()
            
        return instance

class RejectRequestForm(forms.Form):
    """The Admin facing form for rejecting a service request."""
    reason = forms.CharField(label='Raison du refus', max_length=255)

class ShareForm(forms.Form):
    """The Admin facing form for sharing a service request with an agent."""
    email = forms.EmailField(label='Email of the agent to share with')