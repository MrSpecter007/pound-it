from wagtail import hooks


@hooks.register("register_icons")
def register_icons(icons):
    """Used for adding the share icon for specifically sharing the profile to an agent."""
    return icons + ['servicerequests/shareprofile.svg']
