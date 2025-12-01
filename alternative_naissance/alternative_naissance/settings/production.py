from .base import *

DEBUG = False


# # SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "")

# # SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = [os.getenv("ALLOWED_HOSTS", "")]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '21025'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@alternative-naissance.ca')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

try:
    from .local import *
except ImportError:
    pass
