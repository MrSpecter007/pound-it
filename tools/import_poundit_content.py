"""Import the scoped export into a freshly migrated, unused database only.

Run inside the production app container with the content.json path as argument.
Refuses existing content or accounts. Changes are atomic; media is copied separately.
"""
import os
from pathlib import Path
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
import django
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from wagtail.images import get_image_model
from wagtail.models import Page, Site
from poundit.models import PounditHomePage, FacultyMember, Program

fixture = Path(sys.argv[1]).resolve(strict=True)
with transaction.atomic():
    if get_user_model().objects.exists() or get_image_model().objects.exists():
        raise RuntimeError("Destination already contains accounts or images")
    if Page.objects.count() > 2 or Site.objects.count() > 1:
        raise RuntimeError("Destination is not a fresh Wagtail database")
    for app_label in ("core", "poundit", "servicerequests"):
        for model in apps.get_app_config(app_label).get_models():
            if model.objects.exists():
                raise RuntimeError(f"Destination contains {model._meta.label} records")
    # Only the default welcome page/site from Wagtail's initial migration exist.
    Site.objects.all().delete()
    for page in Page.objects.filter(depth=2):
        page.delete()
    call_command("loaddata", str(fixture))
    Page.fix_tree()
    home = PounditHomePage.objects.get()
    for page in home.get_descendants(inclusive=True).specific():
        page.save_revision().publish()
    assert Site.objects.get(is_default_site=True).root_page_id == home.pk
    assert FacultyMember.objects.filter(portrait__isnull=False).count() == 6
    assert Program.objects.count() == 34
print("Imported published Pound It content; legacy data and accounts were excluded.")
