"""
Remove a faculty member who no longer teaches at the studio.

Seeded content, corrected. Deleting the record also clears her rows on
``Program.faculty`` and ``ProgramScheduleEntry.instructors``, which leaves the
Thursday PIBA and Open House sessions without an instructor until someone is
assigned in the admin.
"""

from django.db import migrations


def remove_departed_faculty(apps, schema_editor) -> None:
    FacultyMember = apps.get_model("poundit", "FacultyMember")
    FacultyMember.objects.filter(slug="masha").delete()


def noop(apps, schema_editor) -> None:
    """Not reversible: re-adding the person is an editorial act, not a migration."""


class Migration(migrations.Migration):
    dependencies = [
        ("poundit", "0004_facultymember_short_name"),
    ]

    operations = [
        migrations.RunPython(remove_departed_faculty, noop),
    ]
