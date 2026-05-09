from .base import *  # noqa: F401,F403


DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
