"""
The import ledger.

One row per thing taken from the source site, recording where it came from and
what it became. This is what keeps the importer idempotent: a second run finds
the existing row and updates it instead of creating a duplicate, and anything
that needs a human is left visible rather than silently skipped.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ImportStatus(models.TextChoices):
    IMPORTED = "imported", "Imported"
    PENDING = "pending", "Pending"
    SKIPPED = "skipped", "Skipped"
    NEEDS_REVIEW = "needs_review", "Needs review"


class ImportedObject(models.Model):
    source_url = models.URLField(
        blank=True,
        help_text="Where this came from on the old site.",
    )
    source_identifier = models.CharField(
        max_length=255,
        unique=True,
        help_text="Stable key for this piece of source content, e.g. 'program:lil-cuz'.",
    )

    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    import_status = models.CharField(
        max_length=20, choices=ImportStatus.choices, default=ImportStatus.PENDING
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_imported = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_identifier"]
        verbose_name = "Imported object"
        verbose_name_plural = "Import ledger"
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self) -> str:
        return f"{self.source_identifier} ({self.get_import_status_display()})"

    @property
    def target_label(self) -> str:
        if self.target is None:
            return "-"
        return str(self.target)

    @classmethod
    def record(
        cls,
        source_identifier: str,
        target=None,
        source_url: str = "",
        status: str = ImportStatus.IMPORTED,
        notes: str = "",
    ) -> "ImportedObject":
        """Upsert a ledger row. Safe to call on every run."""
        defaults = {
            "source_url": source_url,
            "import_status": status,
            "notes": notes,
        }
        if target is not None:
            defaults["content_type"] = ContentType.objects.get_for_model(target)
            defaults["object_id"] = target.pk

        entry, _ = cls.objects.update_or_create(
            source_identifier=source_identifier, defaults=defaults
        )
        return entry
