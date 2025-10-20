from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import InscriptionForm

def inscription_view(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre inscription a été enregistrée avec succès.")
            return redirect("/")
    else:
        form = InscriptionForm()

    return render(request, "core/inscription.html", {"form": form})



def mon_compte_view(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username_or_email")
        password = request.POST.get("password")

        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=username_or_email)
            username = user.username
        except User.DoesNotExist:
            username = username_or_email

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Connexion réussie. Bienvenue dans votre espace membre !")
            # Reste sur la page et affiche le message
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")

    return render(request, "core/mon_compte.html")
