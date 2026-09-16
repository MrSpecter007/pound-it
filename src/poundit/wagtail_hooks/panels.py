"""
A dashboard panel for what still needs a person.

The migration deliberately leaves things unfinished rather than guessing —
bios to paste in verbatim, tentative dates to confirm, sessions without an
instructor. Without somewhere to see them, those live only in the output of
a command someone ran once. This puts the list on the admin home page.
"""

from django.utils.functional import cached_property
from wagtail import hooks
from wagtail.admin.site_summary import SummaryItem


class PounditReviewPanel(SummaryItem):
    order = 250
    template_name = "poundit/admin/review_panel.html"

    @cached_property
    def outstanding(self) -> list[dict]:
        from poundit.models import (
            CalendarEntry,
            FacultyMember,
            ImportedObject,
            ImportStatus,
            ProgramScheduleEntry,
            SchoolInquiry,
        )

        items = []

        unhandled = SchoolInquiry.objects.filter(handled=False).count()
        if unhandled:
            items.append(
                {
                    "count": unhandled,
                    "label": "school inquiry awaiting a reply"
                    if unhandled == 1
                    else "school inquiries awaiting a reply",
                    "urgent": True,
                }
            )

        unstaffed = (
            ProgramScheduleEntry.objects.public().filter(instructors__isnull=True).count()
        )
        if unstaffed:
            items.append(
                {
                    "count": unstaffed,
                    "label": "weekly session with no instructor"
                    if unstaffed == 1
                    else "weekly sessions with no instructor",
                    "urgent": True,
                }
            )

        no_bio = FacultyMember.objects.active().filter(full_bio="").count()
        if no_bio:
            items.append(
                {"count": no_bio, "label": "faculty without a biography", "urgent": False}
            )

        no_portrait = FacultyMember.objects.active().filter(portrait__isnull=True).count()
        if no_portrait:
            items.append(
                {"count": no_portrait, "label": "faculty without a portrait", "urgent": False}
            )

        tentative = CalendarEntry.objects.filter(is_tentative=True).count()
        if tentative:
            items.append(
                {"count": tentative, "label": "calendar dates still tentative", "urgent": False}
            )

        flagged = ImportedObject.objects.filter(
            import_status=ImportStatus.NEEDS_REVIEW
        ).count()
        if flagged:
            items.append(
                {"count": flagged, "label": "import records flagged for review", "urgent": False}
            )

        return items

    def get_context_data(self, parent_context) -> dict:
        context = super().get_context_data(parent_context)
        context["outstanding"] = self.outstanding
        return context

    def is_shown(self) -> bool:
        return bool(self.outstanding)


@hooks.register("construct_homepage_summary_items")
def add_poundit_review_panel(request, items) -> None:
    items.append(PounditReviewPanel(request))
