"""Keep the dedicated Pound It admin focused without deleting legacy data."""

from django.conf import settings
from wagtail import hooks


@hooks.register("construct_main_menu")
def focus_poundit_main_menu(request, menu_items):
    if getattr(settings, "POUNDIT_ADMIN_ONLY", False):
        allowed = {"explorer", "pound-it", "images", "settings"}
        menu_items[:] = [item for item in menu_items if item.name in allowed]


@hooks.register("construct_settings_menu")
def focus_poundit_settings_menu(request, menu_items):
    if getattr(settings, "POUNDIT_ADMIN_ONLY", False):
        allowed = {"pound-it-settings", "redirects", "users", "groups"}
        menu_items[:] = [item for item in menu_items if item.name in allowed]
