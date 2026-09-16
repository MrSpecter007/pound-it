from django.apps import AppConfig


class AltNaissanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"

    # The Python package was renamed from `core` so that the tree names this
    # app for the client whose site it is, per docs/PROJECT_TEMPLATE_PROTOCOL.md.
    name = "altnaissance"

    # The *label* stays "core" on purpose. It is written into
    # django_content_type.app_label, into every migration dependency, and into
    # every "core.Model" string reference. Pinning it here makes the rename a
    # pure source-tree change that the database never notices.
    label = "core"
