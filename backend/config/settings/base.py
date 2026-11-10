from pathlib import Path

from decouple import AutoConfig, Csv
from kombu import Exchange, Queue

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
    "apps.hackathons",
    "apps.datathons",
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

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", default=True, cast=bool)
CELERY_TASK_ACKS_LATE = config("CELERY_TASK_ACKS_LATE", default=True, cast=bool)
CELERY_TASK_REJECT_ON_WORKER_LOST = config("CELERY_TASK_REJECT_ON_WORKER_LOST", default=True, cast=bool)
CELERY_WORKER_PREFETCH_MULTIPLIER = config("CELERY_WORKER_PREFETCH_MULTIPLIER", default=1, cast=int)
CELERY_TASK_TIME_LIMIT = config("CELERY_TASK_TIME_LIMIT", default=120, cast=int)
CELERY_TASK_SOFT_TIME_LIMIT = config("CELERY_TASK_SOFT_TIME_LIMIT", default=90, cast=int)
CELERY_BROKER_VISIBILITY_TIMEOUT = config("CELERY_BROKER_VISIBILITY_TIMEOUT", default=3600, cast=int)
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": CELERY_BROKER_VISIBILITY_TIMEOUT,
                                   "socket_connect_timeout": 3, "socket_timeout": 3}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 5
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_QUEUES = (
    Queue("kaggle", Exchange("kaggle", type="direct"), routing_key="kaggle"),
    Queue("kaggle-control", Exchange("kaggle-control", type="direct"), routing_key="kaggle-control"),
)
CELERY_TASK_DEFAULT_QUEUE = "kaggle-control"
CELERY_TASK_ROUTES = {"apps.datathons.tasks.collect_kaggle_profile_task": {"queue": "kaggle"},
                      "apps.datathons.tasks.*": {"queue": "kaggle-control"}}
CELERY_BEAT_SCHEDULE = {
    "kaggle-schedule-due": {"task": "apps.datathons.tasks.schedule_due_kaggle_profiles", "schedule": 60.0},
    "kaggle-dispatch-pending": {"task": "apps.datathons.tasks.dispatch_pending_kaggle_runs", "schedule": 30.0},
    "kaggle-recover-stale": {"task": "apps.datathons.tasks.recover_stale_kaggle_runs", "schedule": 60.0},
    "kaggle-cleanup-runs": {"task": "apps.datathons.tasks.cleanup_old_kaggle_collection_runs", "schedule": 86400.0},
}

KAGGLE_COLLECTION_ENABLED = config("KAGGLE_COLLECTION_ENABLED", default=False, cast=bool)
KAGGLE_PROVIDER_NAME = config("KAGGLE_PROVIDER_NAME", default="disabled")
KAGGLE_SCHEDULED_SYNC_ENABLED = config("KAGGLE_SCHEDULED_SYNC_ENABLED", default=False, cast=bool)
KAGGLE_MANUAL_SYNC_COOLDOWN_SECONDS = config("KAGGLE_MANUAL_SYNC_COOLDOWN_SECONDS", default=3600, cast=int)
KAGGLE_REFRESH_INTERVAL_SECONDS = config("KAGGLE_REFRESH_INTERVAL_SECONDS", default=86400, cast=int)
KAGGLE_SCHEDULER_BATCH_SIZE = config("KAGGLE_SCHEDULER_BATCH_SIZE", default=100, cast=int)
KAGGLE_MAX_ATTEMPTS = config("KAGGLE_MAX_ATTEMPTS", default=3, cast=int)
KAGGLE_RETRY_BASE_DELAY_SECONDS = config("KAGGLE_RETRY_BASE_DELAY_SECONDS", default=30, cast=int)
KAGGLE_RETRY_MAX_DELAY_SECONDS = config("KAGGLE_RETRY_MAX_DELAY_SECONDS", default=900, cast=int)
KAGGLE_RUN_LEASE_SECONDS = config("KAGGLE_RUN_LEASE_SECONDS", default=180, cast=int)
KAGGLE_STALE_RUN_GRACE_SECONDS = config("KAGGLE_STALE_RUN_GRACE_SECONDS", default=3600, cast=int)
KAGGLE_COLLECTION_RUN_RETENTION_DAYS = config("KAGGLE_COLLECTION_RUN_RETENTION_DAYS", default=30, cast=int)


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
CTFTIME_BASE_URL = config(
    "CTFTIME_BASE_URL",
    default="https://ctftime.org/api/v1/",
)
CTFTIME_TIMEOUT_SECONDS = config("CTFTIME_TIMEOUT_SECONDS", default=10.0, cast=float)
CTFTIME_SYNC_ENABLED = config("CTFTIME_SYNC_ENABLED", default=True, cast=bool)
CTFTIME_SYNC_COOLDOWN_SECONDS = config(
    "CTFTIME_SYNC_COOLDOWN_SECONDS", default=3600, cast=int
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
ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS = config(
    "ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS",
    default=ATCODER_SYNC_COOLDOWN_SECONDS,
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

LEETCODE_ALFA_BASE_URL = config(
    "LEETCODE_ALFA_BASE_URL",
    default="https://alfa-leetcode-api.onrender.com",
)
LEETCODE_GRAPHQL_URL = config(
    "LEETCODE_GRAPHQL_URL",
    default="https://leetcode.com/graphql",
)
LEETCODE_GRAPHQL_API_KEY = config(
    "LEETCODE_GRAPHQL_API_KEY",
    default="",
)
LEETCODE_ALFA_CONNECT_TIMEOUT_SECONDS = config(
    "LEETCODE_ALFA_CONNECT_TIMEOUT_SECONDS",
    default=3.05,
    cast=float,
)
LEETCODE_ALFA_READ_TIMEOUT_SECONDS = config(
    "LEETCODE_ALFA_READ_TIMEOUT_SECONDS",
    default=10.0,
    cast=float,
)
LEETCODE_SYNC_ENABLED = config(
    "LEETCODE_SYNC_ENABLED",
    default=True,
    cast=bool,
)
LEETCODE_SYNC_COOLDOWN_SECONDS = config(
    "LEETCODE_SYNC_COOLDOWN_SECONDS",
    default=86400,
    cast=int,
)

ATCODER_PROBLEMS_SYNC_ENABLED = config(
    "ATCODER_PROBLEMS_SYNC_ENABLED",
    default=True,
    cast=bool,
)
ATCODER_PROBLEMS_BASE_URL = config(
    "ATCODER_PROBLEMS_BASE_URL",
    default="https://kenkoooo.com/atcoder/atcoder-api/v3",
)
ATCODER_PROBLEMS_TIMEOUT_SECONDS = config(
    "ATCODER_PROBLEMS_TIMEOUT_SECONDS",
    default=10.0,
    cast=float,
)
ATCODER_PROBLEMS_MIN_REQUEST_INTERVAL_SECONDS = config(
    "ATCODER_PROBLEMS_MIN_REQUEST_INTERVAL_SECONDS",
    default=1.1,
    cast=float,
)
ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC = config(
    "ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC",
    default=2,
    cast=int,
)
ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS = config(
    "ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS",
    default=300,
    cast=int,
)
