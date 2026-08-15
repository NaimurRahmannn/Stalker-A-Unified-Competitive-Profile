from pathlib import Path

from decouple import AutoConfig, Csv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = AutoConfig(search_path=str(BASE_DIR))


SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "apps.accounts",
    "apps.common",
    "apps.connectors",
    "apps.dashboard",
    "apps.profiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DB_NAME = config("DB_NAME", default="")
DB_USER = config("DB_USER", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")
DB_HOST = config("DB_HOST", default="")
DB_PORT = config("DB_PORT", default="")
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.postgresql")

if all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    ),
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True


CODEFORCES_SYNC_COOLDOWN_SECONDS = config(
    "CODEFORCES_SYNC_COOLDOWN_SECONDS",
    default=60,
    cast=int,
)
ATCODER_HISTORY_SYNC_ENABLED = config(
    "ATCODER_HISTORY_SYNC_ENABLED",
    default=True,
    cast=bool,
)
ATCODER_SYNC_COOLDOWN_SECONDS = config(
    "ATCODER_SYNC_COOLDOWN_SECONDS",
    default=3600,
    cast=int,
)
ATCODER_CONNECT_TIMEOUT_SECONDS = config(
    "ATCODER_CONNECT_TIMEOUT_SECONDS",
    default=3.05,
    cast=float,
)
ATCODER_READ_TIMEOUT_SECONDS = config(
    "ATCODER_READ_TIMEOUT_SECONDS",
    default=10.0,
    cast=float,
)
STALKER_EXTERNAL_USER_AGENT = config(
    "STALKER_EXTERNAL_USER_AGENT",
    default=(
        "STALKER/1.0 "
        "(+https://github.com/NaimurRahmannn/Stalker-A-Unified-Competitive-Profile)"
    ),
)
