"""
Tests for routing, legacy redirects and the sitemap.

The sharp edge here is that RoutablePageMixin tries its own routes before child
pages, so an event page slugged the same as an event type would be shadowed by
the filter. That case is tested directly.
"""

import datetime
from typing import override

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site

from poundit.imports import URL_MAP
from poundit.models import EventIndexPage, EventPage, EventType, ProgramIndexPage


class CategoryRoutingTests(TestCase):
    """Program categories are real paths, resolved against the database."""

    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

    def test_index_still_serves(self) -> None:
        self.assertEqual(self.client.get("/programs/", HTTP_HOST="localhost").status_code, 200)

    def test_each_category_has_its_own_path(self) -> None:
        for slug in ("kids-teen", "adult", "competitive", "open-training"):
            with self.subTest(slug=slug):
                response = self.client.get(f"/programs/{slug}/", HTTP_HOST="localhost")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["active_category"], slug)

    def test_category_path_narrows_the_listing(self) -> None:
        response = self.client.get("/programs/adult/", HTTP_HOST="localhost")
        slugs = [c.slug for c, _ in response.context["programs_by_category"]]
        self.assertEqual(slugs, ["adult"])

    def test_unknown_category_is_a_404_not_an_empty_page(self) -> None:
        response = self.client.get("/programs/not-a-category/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 404)

    def test_a_new_category_routes_without_a_code_change(self) -> None:
        from poundit.models import ProgramCategory

        ProgramCategory.objects.create(name="Workshops", slug="workshop-programs")
        response = self.client.get("/programs/workshop-programs/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)

    def test_query_parameter_still_works_for_old_links(self) -> None:
        response = self.client.get("/programs/?category=adult", HTTP_HOST="localhost")
        self.assertEqual(response.context["active_category"], "adult")


class EventTypeRoutingTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        self.index = EventIndexPage.objects.get(slug="events")

    def _event(self, title: str, slug: str, event_type=None) -> EventPage:
        event = EventPage(
            title=title,
            slug=slug,
            start_datetime=timezone.now() + datetime.timedelta(days=30),
            event_type=event_type,
        )
        self.index.add_child(instance=event)
        event.save_revision().publish()
        return event

    def test_event_type_has_its_own_path(self) -> None:
        response = self.client.get("/events/workshop/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_type"], "workshop")

    def test_type_path_narrows_the_listing(self) -> None:
        battle = EventType.objects.get(slug="battle")
        workshop = EventType.objects.get(slug="workshop")
        self._event("Halloween Battle", "halloween-battle", battle)
        self._event("Locking Intensive", "locking-intensive", workshop)

        response = self.client.get("/events/battle/", HTTP_HOST="localhost")
        titles = [event.title for event in response.context["upcoming"]]

        self.assertEqual(titles, ["Halloween Battle"])

    def test_unknown_type_is_a_404(self) -> None:
        response = self.client.get("/events/not-a-type/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 404)

    def test_an_event_page_is_never_shadowed_by_a_type_of_the_same_slug(self) -> None:
        """The guard. Without it this URL would render an empty filter."""
        event = self._event("Workshop", "workshop", EventType.objects.get(slug="workshop"))

        response = self.client.get("/events/workshop/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].id, event.id)

    def test_ordinary_event_pages_still_resolve(self) -> None:
        event = self._event("Halloween Battle", "halloween-battle")
        response = self.client.get("/events/halloween-battle/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].id, event.id)


class LegacyRedirectTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_schedule", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)
        call_command("seed_poundit_redirects", verbosity=0)

    def test_every_legacy_path_is_registered(self) -> None:
        self.assertEqual(Redirect.objects.count(), len(URL_MAP))

    def test_redirects_are_permanent(self) -> None:
        for redirect in Redirect.objects.all():
            with self.subTest(path=redirect.old_path):
                self.assertTrue(redirect.is_permanent)

    def test_crew_pages_land_on_clean_category_paths(self) -> None:
        for legacy, destination in (
            ("/kidsreccrews", "/programs/kids-teen/"),
            ("/adultreccrews", "/programs/adult/"),
            ("/competitivecrews", "/programs/competitive/"),
        ):
            with self.subTest(legacy=legacy):
                response = self.client.get(legacy, HTTP_HOST="localhost")
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], destination)

    def test_a_redirect_followed_through_reaches_a_real_page(self) -> None:
        response = self.client.get("/kidsreccrews", follow=True, HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_category"], "kids-teen")

    def test_destinations_are_paths_not_query_strings(self) -> None:
        for redirect in Redirect.objects.all():
            with self.subTest(path=redirect.old_path):
                self.assertNotIn("?", redirect.redirect_link)

    def test_rerunning_creates_no_duplicates(self) -> None:
        call_command("seed_poundit_redirects", verbosity=0)
        self.assertEqual(Redirect.objects.count(), len(URL_MAP))

    def test_admin_edits_survive_a_rerun(self) -> None:
        redirect = Redirect.objects.get(old_path="/faculty")
        redirect.redirect_link = "/faculty/?edited=1"
        redirect.save()

        call_command("seed_poundit_redirects", verbosity=0)

        redirect.refresh_from_db()
        self.assertEqual(redirect.redirect_link, "/faculty/?edited=1")

    def test_update_flag_restores_the_mapping(self) -> None:
        redirect = Redirect.objects.get(old_path="/faculty")
        redirect.redirect_link = "/wrong/"
        redirect.save()

        call_command("seed_poundit_redirects", "--update", verbosity=0)

        redirect.refresh_from_db()
        self.assertEqual(redirect.redirect_link, "/faculty/")

    def test_dry_run_writes_nothing(self) -> None:
        Redirect.objects.all().delete()
        call_command("seed_poundit_redirects", "--dry-run", verbosity=0)
        self.assertEqual(Redirect.objects.count(), 0)

    def test_command_refuses_before_the_tree_exists(self) -> None:
        from poundit.models import PounditHomePage

        Redirect.objects.all().delete()
        PounditHomePage.objects.all().delete()

        call_command("seed_poundit_redirects", verbosity=0)
        self.assertEqual(Redirect.objects.count(), 0)


class SeoTests(TestCase):
    @override
    def setUp(self) -> None:
        call_command("seed_poundit_taxonomies", verbosity=0)
        call_command("seed_poundit_site", verbosity=0)

    def test_sitemap_is_served(self) -> None:
        response = self.client.get("/sitemap.xml", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])

    def test_sitemap_lists_the_public_pages(self) -> None:
        body = self.client.get("/sitemap.xml", HTTP_HOST="localhost").content.decode()

        for path in ("/programs/", "/schedule/", "/faculty/", "/important-dates/"):
            with self.subTest(path=path):
                self.assertIn(path, body)

    def test_pages_expose_wagtail_seo_fields(self) -> None:
        page = ProgramIndexPage.objects.get(slug="programs")
        page.seo_title = "Hip Hop Classes in Red Deer"
        page.search_description = "Kids, teen and adult hip hop programs."
        page.save_revision().publish()

        response = self.client.get("/programs/", HTTP_HOST="localhost")

        self.assertContains(response, "Hip Hop Classes in Red Deer")
        self.assertContains(response, "Kids, teen and adult hip hop programs.")

    def test_title_falls_back_to_the_page_title(self) -> None:
        response = self.client.get("/schedule/", HTTP_HOST="localhost")
        self.assertContains(response, "<title>Schedule")

    def test_site_is_reachable_on_its_hostname(self) -> None:
        site = Site.objects.get(is_default_site=True)
        self.assertEqual(site.root_page.slug, "poundit")
