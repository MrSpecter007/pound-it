from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-0k(u8qb7urcpn$+65fb_&n7fpqbwvb%!pl7(q^m$_ww51kb)gz"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'localhost'
EMAIL_PORT = 21025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''


try:
    from .local import *
except ImportError:
    pass
