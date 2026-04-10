from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import InscriptionForm
from .forms import ProfilForm
from .models import NewsletterSubscription
from .models import Testimonial


def inscription_view(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre inscription a été enregistrée avec succès.")
            return redirect("dashboard")
    else:
        form = InscriptionForm()

    return render(request, "core/inscription.html", {"form": form})



def mon_compte_view(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username_or_email", "").strip()
        password = request.POST.get("password", "")

        username = username_or_email
        # si on détecte un email, essayer de récupérer l'username associé
        if "@" in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email  # conserver, laisser authenticate échouer ensuite

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Connexion réussie. Bienvenue dans votre espace membre !")
            return redirect("dashboard")
        else:
            messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
    return render(request, "core/mon_compte.html")



@login_required(login_url="/mon-compte/")
def dashboard_view(request):
    user = request.user

    if request.method == "POST":
        form = ProfilForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès.")
            return redirect("dashboard")  # recharge la page proprement
        else:
            messages.error(request, "Une erreur est survenue. Veuillez vérifier les champs.")
    else:
        form = ProfilForm(instance=user)

    return render(request, "core/dashboard.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")  # Redirection vers l’accueil



def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if email:
            # éviter les doublons
            obj, created = NewsletterSubscription.objects.get_or_create(email=email)
            if created:
                messages.success(request, "Merci! Vous êtes inscrit(e) à notre infolettre.")
            else:
                messages.info(request, "Vous êtes déjà inscrit(e).")

    return redirect(request.META.get("HTTP_REFERER", "/"))


def testimonial_create(request):

    if request.method == "POST":

        Testimonial.objects.create(
            client_text=request.POST.get("client_text"),
            category=request.POST.get("category"),
        )
        messages.success(request, "Merci pour votre témoignages !")
        return redirect("/")

    return render(request, "core/testimonial_form.html", {
        "categories": Testimonial.CATEGORY_CHOICES
    })


