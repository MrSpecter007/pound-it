from django.apps import AppConfig


class PounditConfig(AppConfig):
    """
    Pound It Hip Hop Studio.

    Hosted inside the shared Wagtail instance as its own site. Reuses the
    project's shared infrastructure (wagtail.contrib.settings, snippets,
    redirects, images, the ``emails`` app) without modifying ``core``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "poundit"
    verbose_name = "Pound It"

    def ready(self) -> None:
        """Declare the email templates this app sends, editable in the admin."""
        from emails.registry import register_email_template

        variables = """
{{ school_name }} - Name of the school |

{{ contact_name }} - Name of the person who got in touch |

{{ email }} - Their email address |

{{ phone }} - Their phone number |

{{ preferred_dates }} - Dates they suggested |

{{ message }} - Anything else they wrote |

{{ submitted_date }} - Date the inquiry was submitted |
"""

        register_email_template(
            scenario="poundit_school_inquiry_confirmation",
            title="We received your inquiry - Pound It Hip Hop Studios",
            content="""Hi {{ contact_name }},

Thanks for getting in touch about a hip hop residency at {{ school_name }}.

We have your inquiry and someone from the studio will be in contact shortly to
talk through dates and what the residency looks like.

For reference, here is what you sent us:

Preferred dates: {{ preferred_dates }}
Phone: {{ phone }}

Pound It Hip Hop Studios
""",
            available_variables=variables,
            scenario_description=(
                "Sent to the school contact when they submit the residency inquiry form."
            ),
        )

        register_email_template(
            scenario="poundit_school_inquiry_admin_notification",
            title="New school residency inquiry - {{ school_name }}",
            content="""A school has asked about booking a residency.

School: {{ school_name }}
Contact: {{ contact_name }}
Email: {{ email }}
Phone: {{ phone }}
Preferred dates: {{ preferred_dates }}
Submitted: {{ submitted_date }}

Message:
{{ message }}

Open the Wagtail admin to review and mark it handled.
""",
            available_variables=variables,
            scenario_description=(
                "Sent to the studio when a school submits the residency inquiry form."
            ),
        )
