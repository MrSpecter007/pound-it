"""Read-only export of published Pound It content for a fresh staging database.

Run inside the app container: python /tmp/export_poundit_content.py /tmp/poundit-export
Excludes users, sessions, submissions, legacy site data, revisions and audit logs.
The destination must be new. Review counts before transferring the archive.
"""
import json
import os
from pathlib import Path
import sys
import tarfile

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from django.apps import apps
from django.conf import settings
from django.core import serializers
from wagtail.models import Page, Site, Locale, Collection
from wagtail.images import get_image_model
from wagtail.contrib.redirects.models import Redirect
from poundit.models import PounditHomePage

destination = Path(sys.argv[1])
destination.mkdir(mode=0o700, parents=True, exist_ok=False)
home = PounditHomePage.objects.get()
pages = list(home.get_descendants(inclusive=True))
assert all(p.live and not p.has_unpublished_changes for p in pages), "Resolve unpublished changes first"
assert all(p.content_type.app_label == "poundit" for p in pages)
site = Site.objects.get(root_page=home)
root = home.get_ancestors().get(depth=1)
root.numchild = 1
objects = list(Locale.objects.all()) + [root] + pages + [site]
image_ids = set()
excluded = {"schoolinquiry", "importedobject"}
for model in apps.get_app_config("poundit").get_models():
    if model._meta.model_name in excluded:
        continue
    records = model.objects.all()
    if issubclass(model, Page):
        records = records.filter(pk__in=[p.pk for p in pages])
    elif model._meta.model_name == "pounditsettings":
        records = records.filter(site=site)
    for obj in records:
        # This export deliberately requires review if rich content is added;
        # chooser references inside StreamFields need explicit media selection.
        assert not getattr(obj, "body", None), "Review StreamField references before exporting"
        objects.append(obj)
        for field in model._meta.fields:
            if field.is_relation and field.related_model == get_image_model():
                value = getattr(obj, field.attname)
                if value:
                    image_ids.add(value)
images = list(get_image_model().objects.filter(pk__in=image_ids))
collections = {}
for img in images:
    for collection in img.collection.get_ancestors(inclusive=True):
        collections[collection.pk] = collection
objects += sorted(collections.values(), key=lambda c: c.depth) + images
objects += list(Redirect.objects.filter(site=site))
data = json.loads(serializers.serialize("json", objects, use_natural_foreign_keys=True))
for record in data:
    fields = record["fields"]
    for name in ("owner", "locked_by", "latest_revision", "live_revision", "uploaded_by_user"):
        if name in fields:
            fields[name] = None
    if record["model"] == "wagtailcore.page":
        assert fields.get("alias_of") is None, "Page aliases need review"
        fields["locked"] = False
        fields["locked_at"] = None
    if record["model"] == "wagtailcore.site":
        fields.update(hostname="new.pounditdj.com", port=443, is_default_site=True)
    # Site relations use (hostname, port) natural keys, so update references
    # together with the Site row when moving from localhost to staging.
    if fields.get("site") == list(site.natural_key()):
        fields["site"] = ["new.pounditdj.com", 443]
fixture = destination / "content.json"
fixture.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
with tarfile.open(destination / "media.tar.gz", "w:gz") as archive:
    media_root = Path(settings.MEDIA_ROOT).resolve()
    for img in images:
        source = (media_root / img.file.name).resolve()
        assert source.is_relative_to(media_root) and source.is_file()
        archive.add(source, arcname=img.file.name, recursive=False)
summary = {"pages": len(pages), "images": len(images), "fixture_objects": len(data),
           "models": sorted({row["model"] for row in data})}
(destination / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
