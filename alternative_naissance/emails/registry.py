from typing import Dict, List, Any

_default_templates: List[Dict[str, Any]] = []


def register_email_template(scenario: str,
                            title: str,
                            content: str,
                            available_variables: str = "",
                            scenario_description: str = ""
                            ) -> None:
    """
    Register an email template to be created after the app started and migrations are applied..
    
    Call this from other apps' AppConfig.ready() (or module import during startup)
    to declare a template. This function only collects declarations; creation
    in DB happens after migrations (post_migrate).
    
    Args:
        scenario: Unique identifier for this template in snake case (e.g., "user_request_submitted")
        scenario_description: Human-readable description of the scenario (e.g., "Email sent to user when their request is submitted")
        title: Default email subject (can include template variables)
        content: Default email body (can include template variables)
        available_variables: Human-readable description of list of variables that can be used in the template.
    """
    _default_templates.append({
        "scenario": scenario,
        "scenario_description": scenario_description,
        "title": title,
        "content": content,
        "available_variables": available_variables,
    })


def get_declared_templates() -> List[Dict[str, Any]]:
    # Return a copy
    return list(_default_templates)
