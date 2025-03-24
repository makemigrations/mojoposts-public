import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default='aweoifjwi39a0f9afa9wfaw09898098a0f8wefa08w8vv89b8b0se8rf0rt8aeeereastr89e0aser4adefadfadsfasdfb09bjafjafwefambEADAESBAadsdEABNNFSGRSFfstrdsf')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

if 'CODESPACE_NAME' in os.environ:
    codespace_name = config("CODESPACE_NAME")
    codespace_domain = config("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    CSRF_TRUSTED_ORIGINS = [f'https://{codespace_name}-8000.{codespace_domain}']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "django_ratelimit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

X_FRAME_OPTIONS = "ALLOW-FROM preview.app.github.dev"

ROOT_URLCONF = "hello_world.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "hello_world" / "templates"],
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

WSGI_APPLICATION = "hello_world.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATICFILES_DIRS = [
    BASE_DIR / "hello_world" / "static",
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "hello_world" / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "hello_world" / "media"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

COINSET_API_BASE = "https://api.coinset.org"

# You can also add other related settings here
COINSET_SETTINGS = {
    'MAX_PAGES': 100,
    'DEFAULT_PAGE_SIZE': 50,
    'CACHE_TIMEOUT': 300,  # 5 minutes
}

# Puzzle Hash for the application
PUZZLE_HASH = "0x00cbc7bcd21ae5cc6f4691d9367f1671bb99a60ce02409d9966017778c62d204"

# Blocked words for content moderation
BLOCKED_WORDS = ["scam", "fake", "spam", "fraud"]

# Blocked patterns for content moderation
BLOCKED_PATTERNS = ["http://", "https://", "www."]

STREAM_DELAY = 1  # Delay in seconds for streaming responses

