import os

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "houseprice"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "10")),
            "sslmode": os.environ.get("DB_SSL_MODE", "prefer"),
        },
    }
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = os.environ.get("SECURE_COOKIES", "false").lower() == "true"
CSRF_COOKIE_SECURE = os.environ.get("SECURE_COOKIES", "false").lower() == "true"


def check_database_connection():
    """Health check: verify PostgreSQL is reachable.

    Returns (ok: bool, message: str).
    Call from a management command or a health-check endpoint.
    """
    from django.db import connections
    from django.db.utils import OperationalError

    db_conn = connections["default"]
    try:
        db_conn.ensure_connection()
        return True, "Database connection OK"
    except OperationalError as exc:
        return False, f"Database connection failed: {exc}"
    finally:
        db_conn.close()
