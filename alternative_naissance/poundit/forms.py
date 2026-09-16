"""
Public forms for Pound It.

Follows the project's existing convention: a plain ModelForm, validated in the
view, with no third-party form machinery.
"""

from typing import Any

from django import forms

from poundit.models import SchoolInquiry


class SchoolInquiryForm(forms.ModelForm):
    """
    The single school residency inquiry.

    The source site renders the same form twice on one page. This is the only
    one, and it posts back to the page it appears on.
    """

    # Bots fill every field they find; people never see this one.
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        label="",
    )

    class Meta:
        model = SchoolInquiry
        fields = ["school_name", "contact_name", "email", "phone", "preferred_dates", "message"]
        labels = {
            "school_name": "School name",
            "contact_name": "Contact",
            "email": "Email",
            "phone": "Phone",
            "preferred_dates": "Preferred dates",
            "message": "Anything else we should know",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            "preferred_dates": forms.TextInput(
                attrs={"placeholder": "e.g. week of 12 January, or any week in March"}
            ),
        }
        # Model help text is written for studio staff in the admin. None of it
        # belongs on the public form.
        help_texts = {
            "school_name": "",
            "contact_name": "",
            "email": "",
            "phone": "",
            "preferred_dates": "",
            "message": "",
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["school_name"].required = True
        self.fields["contact_name"].required = True
        self.fields["email"].required = True

    def clean_website(self) -> str:
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("This submission looks automated.")
        return ""
