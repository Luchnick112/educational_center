from .settings_base import *  # noqa: F403

from django.core.exceptions import ImproperlyConfigured


DEBUG = env_bool("DEBUG", False)  # noqa: F405

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")  # noqa: F405
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")  # noqa: F405

if not SECRET_KEY or SECRET_KEY == "django-insecure-dev-only-change-me":  # noqa: F405
    raise ImproperlyConfigured("SECRET_KEY must be set for production.")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set for production.")

DATABASES = {
    "default": postgres_database_config(host_default="db"),  # noqa: F405
}

MIDDLEWARE = [
    item for item in MIDDLEWARE  # noqa: F405
    if item != "core.middleware.DevCorsMiddleware"
]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)  # noqa: F405
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)  # noqa: F405
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
