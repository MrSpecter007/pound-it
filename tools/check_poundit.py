"""Read-only integration checks for the installed Pound It frontend.

Run from /app inside the existing container. Page records and inquiries are never
created or changed. Wagtail may generate image renditions as normal rendering does.
Optional preview output contains disposable, clearly test-only form/event states.
"""
import argparse
from datetime import timedelta
from pathlib import Path
import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alternative_naissance.settings.dev")
import django
django.setup()
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.utils import timezone
from wagtail.models import Site
from poundit.forms import SchoolInquiryForm
from poundit.models import EventPage, PounditHomePage, PounditSettings, ProgramCategory, EventType, SchoolProgramsPage


def validate(markup, label):
    soup = BeautifulSoup(markup, "html.parser")
    assert len(soup.select("main")) == 1, (label, "main landmark")
    assert len(soup.select("h1")) == 1, (label, "one h1")
    ids = [node["id"] for node in soup.select("[id]")]
    assert len(ids) == len(set(ids)), (label, "duplicate IDs")
    assert all(node.has_attr("alt") for node in soup.select("img")), (label, "image alt")
    assert soup.select_one('link[href*="poundit/poundit.css"]'), (label, "design stylesheet")
    assert not soup.select('a[href=""], a[href="#"]'), (label, "empty links")
    assert not any(bad in markup for bad in ("\u00e2\u2020", "\u00c2\u00a9", "\ufffd")), (label, "encoding")
    assert "{{" not in markup and "{%" not in markup, (label, "unrendered template")
    return soup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    root = Path("templates/poundit")
    for path in root.rglob("*.html"):
        engines["django"].get_template(str(path.relative_to("templates")))
    print(f"Compiled {len(list(root.rglob('*.html')))} templates.")

    client = Client(HTTP_HOST="localhost:8000")
    home = PounditHomePage.objects.get(slug="poundit")
    routes = {"/"}
    routes.update(page.get_url(request=None) for page in home.get_descendants().live().specific())
    routes = {url for url in routes if url and url.startswith("/")}
    routes.update(f"/programs/{cat.slug}/" for cat in ProgramCategory.objects.all())
    routes.update(f"/events/{kind.slug}/" for kind in EventType.objects.all())
    routes.add("/important-dates/?category=closure")
    soups = {}
    for route in sorted(routes):
        response = client.get(route)
        assert response.status_code == 200, (route, response.status_code)
        soups[route] = validate(response.content.decode(), route)
    # Check all same-site navigation, including snippet fragment targets.
    from urllib.parse import urlsplit
    targets = {node["href"] for soup in soups.values() for node in soup.select('a[href^="/"]')}
    for target in sorted(targets):
        parts = urlsplit(target)
        route = parts.path + (("?" + parts.query) if parts.query else "")
        if route not in soups:
            response = client.get(route)
            assert response.status_code == 200, (target, response.status_code)
            soups[route] = validate(response.content.decode(), target)
        if parts.fragment:
            assert soups[route].find(id=parts.fragment), (target, "missing fragment")
    print(f"Rendered {len(soups)} live routes; {len(targets)} local link targets resolve.")

    school = SchoolProgramsPage.objects.first()
    request = RequestFactory().get("/school-programs/", HTTP_HOST="localhost:8000")
    request.user = AnonymousUser()
    form = SchoolInquiryForm(data={"email": "invalid"})
    assert not form.is_valid()
    context = school.get_context(request)
    context.update({"form": form, "submitted": False})
    error_html = render_to_string(school.template, context, request=request)
    soup = validate(error_html, "invalid inquiry")
    assert len(soup.select("form")) == 1
    assert soup.select_one('.pi-form-errors[role="alert"][tabindex="-1"]')
    assert soup.select_one('input[aria-invalid="true"]')
    assert soup.select_one('input[name="website"][type="hidden"]')
    assert soup.select_one('input[name="csrfmiddlewaretoken"]')
    for field in soup.select('input:not([type="hidden"]), textarea, select'):
        assert soup.find("label", attrs={"for": field.get("id")}), field.get("name")
    print("Inquiry: one form, labels, honeypot, CSRF and linked server errors verified.")

    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        (args.preview_dir / "form_errors.html").write_text(error_html, encoding="utf-8")
        no_js = soups["/"]
        for node in no_js.select("script"):
            node.decompose()
        (args.preview_dir / "no_js_home.html").write_text(str(no_js), encoding="utf-8")

    for status, past in [("scheduled", False), ("scheduled", True), ("cancelled", False), ("sold_out", False), ("postponed", False)]:
        event = EventPage(title="Frontend QA event", slug="frontend-qa", status=status,
                          start_datetime=timezone.now() + timedelta(days=-2 if past else 2),
                          registration_url="https://example.invalid/qa-register")
        html = render_to_string("poundit/event_page.html", {"page": event}, request=request)
        soup = validate(html, f"event {status} past={past}")
        assert bool(soup.select_one('.pi-facts a[href="https://example.invalid/qa-register"]')) == (status == "scheduled" and not past)
        if args.preview_dir and past:
            (args.preview_dir / "event_archive.html").write_text(html, encoding="utf-8")
    print("Registration appears only for future scheduled events.")

    studio = PounditSettings.for_site(Site.find_for_request(request))
    if studio.logo:
        markup = render_to_string("poundit/components/image.html", {"image": studio.logo, "ratio": "hero", "eager": True})
        image = BeautifulSoup(markup, "html.parser")
        assert image.select_one('picture source[media="(min-width: 801px)"][srcset]')
        assert image.select_one('img[srcset][fetchpriority="high"]')
        print("Actual Wagtail image rendered desktop/mobile crops and responsive srcsets.")
    print("All frontend integration checks passed.")


if __name__ == "__main__":
    main()
