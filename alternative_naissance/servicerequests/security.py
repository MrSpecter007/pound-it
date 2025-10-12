from django.contrib.auth.models import User

def can_modify_servicerequests(user: User) -> bool:
    return user.is_superuser