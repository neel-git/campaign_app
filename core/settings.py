"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from utils.config_loader import ConfigurationLoader


config = ConfigurationLoader()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get("application.secret_key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.get("application.debug", False)

ALLOWED_HOSTS = config.get("application.allowed_hosts", [])


# Application definition

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
]

EXTERNAL_APPS = ["practices", "authentication", "campaigns", "usermessages"]

INSTALLED_APPS += EXTERNAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "authentication.middleware.CustomAuthMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "authentication.middleware.CustomAuthMiddleware",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": config.get("database.engine"),
        "NAME": config.get("database.name"),
        "USER": config.get("database.user"),
        "PASSWORD": config.get("database.password"),
        "HOST": config.get("database.host"),
        "PORT": config.get("database.port"),
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DATABASES['default']['USER']}:"
    f"{DATABASES['default']['PASSWORD']}@"
    f"{DATABASES['default']['HOST']}:"
    f"{DATABASES['default']['PORT']}/"
    f"{DATABASES['default']['NAME']}"
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "authentication.backends.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds
SESSION_SAVE_EVERY_REQUEST = True

CORS_ALLOWED_ORIGINS = config.get("cors.allowed_origins", [
    "http://localhost:5173",
    "https://campaign-app.vercel.app"
])

CORS_ALLOW_CREDENTIALS = config.get("cors.allow_credentials", True)

CSRF_TRUSTED_ORIGINS = [
    "https://campaignapp-production.up.railway.app",
    "http://localhost:5173",
    "https://campaign-app-frontend-liard.vercel.app/"
]

CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CORS_ALLOW_METHODS = config.get(
    "cors.allowed_methods", ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

CORS_ALLOW_HEADERS = config.get(
    "cors.allowed_headers",
    [
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
    ],
)

CELERY_BROKER_URL = config.get("celery.broker_url")
CELERY_RESULT_BACKEND = config.get("celery.result_backend")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
