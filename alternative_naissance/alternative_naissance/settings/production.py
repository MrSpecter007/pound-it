"""
Production settings.

Everything secret or environment-specific is read from the environment. There
are no usable defaults here on purpose: a missing SECRET_KEY should stop the
container starting, not quietly fall back to something weak.
"""

from .base import *  # noqa: F403


def _csv(name: str) -> list[str]:
    """Read a comma-separated environment variable into a list."""
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


DEBUG = False

# No fallback. Django raises ImproperlyConfigured on an empty key, which is the
# failure we want: loud, at startup, rather than a site signing cookies weakly.
SECRET_KEY = os.getenv("SECRET_KEY", "")

# Must be a list. Wrapping the raw variable in [] gives one bogus host such as
# "a.com,b.com", which matches nothing and returns 400 for every request.
ALLOWED_HOSTS = _csv("ALLOWED_HOSTS")

# Django 4+ rejects cross-origin POSTs whose origin is not listed here. Without
# it the Wagtail admin login and the school inquiry form both fail behind TLS.
# Entries need the scheme: https://pounditdj.com
CSRF_TRUSTED_ORIGINS = _csv("CSRF_TRUSTED_ORIGINS")

# --------------------------------------------------------------------------
# Transport security
#
# The app sits behind a TLS-terminating reverse proxy, so it must be told how
# to recognise a request that arrived over HTTPS before it can redirect safely.
# --------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Start this low (300) for the first day. HSTS is cached by browsers and is
# painful to walk back if the certificate is not yet solid.
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "300"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# Used in notification emails and some admin links, so it has to be the real
# public origin rather than a placeholder.
WAGTAILADMIN_BASE_URL = os.getenv("WAGTAILADMIN_BASE_URL", "")

# --------------------------------------------------------------------------
# Logging: to stdout, for `docker compose logs`.
# --------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "poundit": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Static storage is configured in base.py via STORAGES. The old
# STATICFILES_STORAGE setting is ignored on Django 5.2 and is deliberately
# not set here, so nobody trusts a line that does nothing.

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
