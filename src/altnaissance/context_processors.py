from .models import Menu

def menu_context(request):
    menu = Menu.objects.first()  # ou filtre si plusieurs menus
    return {
        "main_menu": menu
    }