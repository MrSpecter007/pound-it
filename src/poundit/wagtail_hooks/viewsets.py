"""
Admin registration for Pound It.

Everything lives under one "Pound It" menu rather than scattering six entries
across the sidebar, which also keeps it clear of Alternative Naissance's own
sections. Order runs from what staff touch daily down to what they set up once.
"""

from django.conf import settings
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from poundit.models import (
    CalendarCategory,
    CalendarEntry,
    DanceStyle,
    EventType,
    FacultyMember,
    ImportedObject,
    Program,
    ProgramCategory,
    SchoolInquiry,
    Season,
    StudioRoom,
    TrainingLevel,
)

# --------------------------------------------------------------------------
# Day to day
# --------------------------------------------------------------------------


class ProgramViewSet(SnippetViewSet):
    model = Program
    icon = "group"
    menu_label = "Programs"
    list_display = [
        "title",
        "category",
        "level",
        "age_display",
        "tuition_display",
        "schedule_display",
        "is_public",
        "active",
    ]
    list_filter = ["category", "level", "is_public", "active", "featured", "audition_required"]
    search_fields = ["title", "short_description"]
    ordering = ["sort_order", "title"]
    list_per_page = 50


class FacultyViewSet(SnippetViewSet):
    model = FacultyMember
    icon = "user"
    menu_label = "Faculty"
    list_display = ["display_name", "role", "is_occasional", "featured", "active", "sort_order"]
    list_filter = ["is_occasional", "featured", "active"]
    search_fields = ["name", "dance_name", "role", "short_bio"]
    ordering = ["sort_order", "name"]


class CalendarEntryViewSet(SnippetViewSet):
    model = CalendarEntry
    icon = "calendar-alt"
    menu_label = "Season calendar"
    list_display = ["title", "date_display", "category", "is_tentative", "season"]
    list_filter = ["category", "season", "is_tentative", "featured"]
    search_fields = ["title", "description"]
    ordering = ["start_date", "title"]
    list_per_page = 50


class SchoolInquiryViewSet(SnippetViewSet):
    """
    Inquiry submissions.

    Adding one by hand makes no sense - they only arrive from the public form -
    but staff do need to edit, to tick "handled" and leave internal notes.
    """

    model = SchoolInquiry
    icon = "mail"
    menu_label = "School inquiries"
    list_display = [
        "school_name",
        "contact_name",
        "email",
        "preferred_dates",
        "handled",
        "created_at",
    ]
    list_filter = ["handled"]
    search_fields = ["school_name", "contact_name", "email"]
    ordering = ["-created_at"]
    add_view_enabled = False
    inspect_view_enabled = True


# --------------------------------------------------------------------------
# Set up once, edit rarely
# --------------------------------------------------------------------------


class SeasonViewSet(SnippetViewSet):
    model = Season
    icon = "date"
    menu_label = "Seasons"
    list_display = ["label", "start_date", "end_date", "is_current"]
    search_fields = ["label"]


class ProgramCategoryViewSet(SnippetViewSet):
    model = ProgramCategory
    icon = "folder-open-inverse"
    menu_label = "Program categories"
    list_display = ["name", "slug", "sort_order"]
    search_fields = ["name"]
    ordering = ["sort_order", "name"]


class TrainingLevelViewSet(SnippetViewSet):
    model = TrainingLevel
    icon = "list-ul"
    menu_label = "Training levels"
    list_display = [
        "display_label",
        "colour_identifier",
        "age_label",
        "show_in_legend",
        "sort_order",
    ]
    search_fields = ["name", "display_label"]
    ordering = ["sort_order", "name"]


class DanceStyleViewSet(SnippetViewSet):
    model = DanceStyle
    icon = "tag"
    menu_label = "Dance styles"
    list_display = ["name", "short_description", "sort_order"]
    search_fields = ["name", "short_description"]
    ordering = ["sort_order", "name"]


class StudioRoomViewSet(SnippetViewSet):
    model = StudioRoom
    icon = "home"
    menu_label = "Studio rooms"
    list_display = ["name", "slug", "is_active", "sort_order"]
    search_fields = ["name"]
    ordering = ["sort_order", "name"]


class EventTypeViewSet(SnippetViewSet):
    model = EventType
    icon = "pick"
    menu_label = "Event types"
    list_display = ["name", "slug", "sort_order"]
    search_fields = ["name"]
    ordering = ["sort_order", "name"]


class CalendarCategoryViewSet(SnippetViewSet):
    model = CalendarCategory
    icon = "tag"
    menu_label = "Calendar categories"
    list_display = ["name", "slug", "sort_order"]
    search_fields = ["name"]
    ordering = ["sort_order", "name"]


class ImportLedgerViewSet(SnippetViewSet):
    """
    Where every imported object came from, and what still needs a human.

    Read-only: the importer owns these rows. Filter by status to find the
    content flagged for review.
    """

    model = ImportedObject
    icon = "doc-empty"
    menu_label = "Import ledger"
    list_display = [
        "source_identifier",
        "target_label",
        "import_status",
        "source_url",
        "last_imported",
    ]
    list_filter = ["import_status"]
    search_fields = ["source_identifier", "source_url", "notes"]
    add_view_enabled = False
    edit_view_enabled = False
    inspect_view_enabled = True
    list_per_page = 50


class PounditGroup(SnippetViewSetGroup):
    """One sidebar entry for the whole studio."""

    menu_label = "Pound It"
    menu_icon = "group"
    menu_order = 290

    def get_submenu_items(self):
        if not getattr(settings, "POUNDIT_ADMIN_ONLY", False):
            return super().get_submenu_items()
        return [
            viewset.get_menu_item(order=index)
            for index, viewset in enumerate(self.registerables, start=1)
            if not isinstance(viewset, ImportLedgerViewSet)
        ]

    items = (
        # Daily
        ProgramViewSet,
        FacultyViewSet,
        CalendarEntryViewSet,
        SchoolInquiryViewSet,
        # Setup
        SeasonViewSet,
        ProgramCategoryViewSet,
        TrainingLevelViewSet,
        DanceStyleViewSet,
        StudioRoomViewSet,
        EventTypeViewSet,
        CalendarCategoryViewSet,
        # Migration
        ImportLedgerViewSet,
    )


register_snippet(PounditGroup)
