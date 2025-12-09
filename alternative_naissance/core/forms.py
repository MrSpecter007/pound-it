from django import forms
from .models import Inscription
from django.contrib.auth.models import User

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
    
    def save(self, commit=True):
        """
        Sauve l'objet Inscription puis crée (ou met à jour) un User Django
        avec le même email/pseudonyme et le mot de passe haché.
        """
        inscription = super().save(commit=False)

        # Sauvegarde Inscription
        if commit:
            inscription.save()

        # Créer ou mettre à jour l'utilisateur Django
        username = inscription.pseudonyme if inscription.pseudonyme else inscription.courriel.split("@")[0]
        email = inscription.courriel

        user, created = User.objects.get_or_create(username=username, defaults={
            "first_name": inscription.prenom or "",
            "last_name": inscription.nom or "",
            "email": email or "",
        })

        # Si l'email existait déjà sur un autre user, on peut essayer de le retrouver
        if not created and not user.email and email:
            user.email = email

        # Toujours (ré)mettre à jour le nom et le prénom si besoin
        user.first_name = inscription.prenom or user.first_name
        user.last_name = inscription.nom or user.last_name

        # Set password (utilise create_user / set_password pour le hachage)
        user.set_password(inscription.mot_de_passe)
        user.save()

        return inscription


class ProfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]