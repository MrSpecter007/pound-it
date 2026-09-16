"""Admin branding checks and optional screenshots fixtures in a separate test DB.

Inside /app: python /tmp/check_poundit_admin.py
Set POUNDIT_ADMIN_PREVIEW_DIR to write disposable HTML using sample test data.
No production users, passwords, permissions or content are changed.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alternative_naissance.settings.dev')
import django
django.setup()

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import get_runner
from wagtail.users.models import UserProfile
from poundit.models import Program


class AdminBrandingChecks(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_poundit_taxonomies', verbosity=0)
        call_command('seed_poundit_site', verbosity=0)
        call_command('seed_poundit_schedule', verbosity=0)
        cls.editor = get_user_model().objects.create(
            username='design-review', first_name='Studio', last_name='Editor',
            is_staff=True, is_superuser=True, is_active=True,
        )
        cls.editor.set_unusable_password()
        cls.editor.save()

    def check_page(self, response, name, logo=True):
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('link[href$="poundit/admin.css"]')), 1)
        self.assertIn('Pound It Studio Admin', soup.title.text)
        self.assertTrue(soup.select_one('link[rel="icon"][href$="poundit/images/logo.png"]'))
        if logo:
            self.assertTrue(soup.select_one('img.pi-admin-logo[alt="Pound It Hip Hop Studios"]'))
        self.assertNotIn('Alt_naissance_Couleur', response.content.decode())
        self.assertFalse(soup.select('link[href$="poundit/poundit.css"]'))
        preview = os.environ.get('POUNDIT_ADMIN_PREVIEW_DIR')
        if preview:
            directory = Path(preview)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / (name + '.html')).write_text(str(soup), encoding='utf-8')
        return soup

    def test_login_and_recovery_keep_their_forms(self):
        soup = self.check_page(self.client.get('/admin/login/?next=/admin/'), 'login')
        self.assertTrue(soup.select_one('input[name="csrfmiddlewaretoken"]'))
        self.assertTrue(soup.select_one('input[name="next"][value="/admin/"]'))
        self.assertTrue(soup.select_one('input[name="username"]'))
        self.assertTrue(soup.select_one('input[name="password"]'))
        self.check_page(self.client.get('/admin/password_reset/'), 'password_reset', logo=False)

    def test_dashboard_list_and_editor_in_both_themes(self):
        self.client.force_login(self.editor)
        program = Program.objects.get(slug='lil-cuz')
        for theme in ['light', 'dark']:
            profile = UserProfile.get_for_user(self.editor)
            profile.theme = theme
            profile.save()
            for name, url in [
                ('dashboard', '/admin/'),
                ('programs', '/admin/snippets/poundit/program/'),
                ('editor', f'/admin/snippets/poundit/program/edit/{program.pk}/'),
                ('images', '/admin/images/'),
            ]:
                with self.subTest(theme=theme, page=name):
                    soup = self.check_page(self.client.get(url), f'{name}_{theme}')
                    self.assertIn(f'w-theme-{theme}', soup.html['class'])
                    if name == 'dashboard':
                        self.assertIn('Studio dashboard', soup.h1.text)
                    if name == 'editor':
                        self.assertTrue(soup.select_one('input[name="csrfmiddlewaretoken"]'))
                        self.assertTrue(soup.select_one('input[name="title"]'))


if __name__ == '__main__':
    runner = get_runner(settings)(verbosity=1, interactive=False)
    sys.exit(bool(runner.run_tests(['__main__.AdminBrandingChecks'])))
