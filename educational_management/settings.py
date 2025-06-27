from pathlib import Path
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import redis
from django.conf import settings
from pymongo import MongoClient
from decouple import config

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-default-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]


CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_yasg",
    "corsheaders",
    "django_celery_beat",
    # Applications
    "user_management.apps.UserManagementConfig",
    "payment_management.apps.PaymentManagementConfig",
    "institution",
    "quiz",
    "attendance",
    "notice",
    "syllabus",
    "homework",
    "exam",
    "result",
    "scholarship",
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
    "django.middleware.security.SecurityMiddleware",
]

ROOT_URLCONF = "educational_management.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "user_management", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "educational_management.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

USE_SQLITE = os.getenv("DJANGO_DEBUG", "True") == "True"

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": "db",
            "PORT": "5432",
        }
    }


# mongo_client = MongoClient(os.getenv("MONGO_URI"))
# mongo_db = mongo_client["educational_management_mongo"]

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "user_management.User"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=6),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = 0
REDIS_CLIENT = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


# Use LocMemCache for tests, RedisCache for production
if os.getenv("DJANGO_TEST", "False") == "True":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }


# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER")
CELERY_RESULT_BACKEND = os.getenv("CELERY_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Dhaka"
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULER = (
    "django_celery_beat.schedulers:DatabaseScheduler"  # For Celery Beat
)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "secretgiggle3@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "fomd dmal plap kvhb")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# CELERY_BEAT_SCHEDULE = {
#     'send-salary-notifications': {
#         'task': 'department.tasks.send_salary_notifications',
#         'schedule': crontab(day_of_month=1, hour=9, minute=0),  # Run on the 1st of every month at 9 AM
#     },
#     'sync-attendance-to-postgres': {  # From previous attendance implementation
#         'task': 'department.tasks.sync_attendance_to_postgres',
#         'schedule': crontab(hour=0, minute=0),  # Midnight daily
#     },
# }
# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",  # Changed from INFO
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "debug.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",  # Changed from INFO
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "user_management": {
            "handlers": ["file", "console"],
            "level": "DEBUG",  # Changed from INFO
            "propagate": False,
        },
        "celery": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "payment_management": {
            "handlers": ["file", "console"],
            "level": "DEBUG",  # Changed from INFO
            "propagate": False,
        },
    },
}

SMS_USERNAME = os.getenv("SMS_USERNAME", "rajuhosseng@gmail.com")
SMS_API_KEY = os.getenv("SMS_API_KEY", "V0VDKBSI84ECAWL")
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "8809601010352")
OTP_EXPIRY_TIME = int(os.getenv("OTP_EXPIRY_TIME", 105))  # 1.45 minutes default
OTP_REQUEST_COOLDOWN = int(os.getenv("OTP_REQUEST_COOLDOWN", 120))  # 2 minutes default


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static and Media Files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


BKASH_APP_KEY = config("BKASH_APP_KEY")
BKASH_APP_SECRET = config("BKASH_APP_SECRET")
BKASH_USERNAME = config("BKASH_USERNAME")
BKASH_PASSWORD = config("BKASH_PASSWORD")
BKASH_BASE_URL = config("BKASH_BASE_URL")
BKASH_CALLBACK_URL = config("BKASH_CALLBACK_URL")


if not all(
    [BKASH_APP_KEY, BKASH_APP_SECRET, BKASH_USERNAME, BKASH_PASSWORD, BKASH_BASE_URL]
):
    raise ValueError("Missing bKash configuration in environment variables")
