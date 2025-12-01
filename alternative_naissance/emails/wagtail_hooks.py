from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from emails.models import EmailTemplate


@register_snippet
class EmailTemplateViewSet(SnippetViewSet):
    model = EmailTemplate

    panels = [
        FieldPanel('scenario', read_only=True),
        FieldPanel('scenario_description', read_only=True),
        FieldPanel('available_variables', read_only=True),
        FieldPanel('title'),
        FieldPanel('content'),
    ]

    menu_icon = 'mail'
    icon = 'mail'
    list_display = ('scenario', 'scenario_description')
    add_to_admin_menu = True
