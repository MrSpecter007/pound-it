from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from wagtail import hooks
from wagtail.admin.panels import FieldPanel
from wagtail.admin.widgets import ListingButton
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


@hooks.register('construct_snippet_listing_buttons')
def remove_delete_button_in_email_template(buttons: list[ListingButton], snippet, user):
    if issubclass(type(snippet), EmailTemplate):
        for button in buttons:
            if button.label == 'Delete':
                buttons.remove(button)


@hooks.register("before_bulk_action")
def disallow_delete_email_template(request, action_type, objects: list,
                                   action_class_instance) -> HttpResponseRedirect | None:
    if action_type == 'delete' and len(objects) > 0 and issubclass(type(objects[0]), EmailTemplate):
        messages.error(request, "Vous ne pouvez pas supprimer les Modèles du Courrier")
        return redirect("/admin/snippets/emails/emailtemplate/")
    else:
        return None
