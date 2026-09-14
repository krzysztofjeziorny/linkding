import os
from email.utils import getaddresses
from pathlib import Path

import environ

# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env file
env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

DEBUG = env.bool("DEBUG")
SECRET_KEY = env("DJANGO_SECRET_KEY")
ADMINS = getaddresses([env("DJANGO_ADMINS")])
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL")
DEFAULT_FROM_EMAIL = env("DJANGO_SERVER_EMAIL")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
TIME_ZONE = "Europe/Vienna"


default_loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "bookmarks.context_processors.toasts",
                "bookmarks.context_processors.app_version",
            ],
            "loaders": default_loaders if DEBUG else cached_loaders,
        },
    },
]

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {"default": env.db("DJANGO_DATABASE_URL")}
USE_SQLITE_ICU_EXTENSION = False
