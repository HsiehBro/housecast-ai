import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
