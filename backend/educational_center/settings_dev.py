from .settings_base import *  # noqa: F403


DEBUG = env_bool("DEBUG", True)  # noqa: F405

ALLOWED_HOSTS = env_list(  # noqa: F405
    "ALLOWED_HOSTS",
    ["localhost", "127.0.0.1", "0.0.0.0"],
)

DATABASES = {
    "default": postgres_database_config(host_default="localhost"),  # noqa: F405
}

DEV_CORS_ALLOWED_ORIGINS = env_list(  # noqa: F405
    "DEV_CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5190",
        "http://127.0.0.1:5190",
    ],
)

