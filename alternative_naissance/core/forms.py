from django import forms
from .models import Inscription

class InscriptionForm(forms.ModelForm):
    mot_de_passe_confirmation = forms.CharField(
        widget=forms.PasswordInput(),
        label="Confirmez le mot de passe"
    )

    class Meta:
        model = Inscription
        fields = [
            "prenom", "nom", "courriel", "pseudonyme",
            "mot_de_passe", "mot_de_passe_confirmation",
            "adresse", "ville", "province", "code_postal",
            "telephone_maison", "cellulaire", "telephone_travail", "numero_poste"
        ]
        widgets = {
            "mot_de_passe": forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        mot_de_passe = cleaned_data.get("mot_de_passe")
        confirmation = cleaned_data.get("mot_de_passe_confirmation")

        if mot_de_passe != confirmation:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data
