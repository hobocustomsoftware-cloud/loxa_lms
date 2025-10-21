import os

from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure")
# DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
DEBUG = os.getenv("DEBUG","").lower() in ("1","true","yes")

# ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")
ALLOWED_HOSTS = ['lms.ai1.com.mm', 'web', 'localhost']





# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_simplejwt",

    "api",
    "orgs",

    "social_django",
    "corsheaders",

    "drf_yasg", 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

MIDDLEWARE.insert(1, "orgs.middleware.current_org_middleware")



ROOT_URLCONF = 'loxa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'loxa.wsgi.application'

CSRF_TRUSTED_ORIGINS = [
    'https://lms.ai1.com.mm','http://localhost',
    'http://127.0.0.1',
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }

    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "loxa_db"),
        "USER": os.getenv("POSTGRES_USER", "loxa_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "loxa@loxa"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "OPTIONS": {"connect_timeout": 5},
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "/data/static"          # <- docker volume mount နဲ့တူရမယ်
STATICFILES_DIRS = [
    BASE_DIR / "static",              # project-level assets (optional)
    BASE_DIR / "loxa" / "static",     # app-level assets (if you have)
    BASE_DIR / "api" / "static",      # app-level assets (if you have)
]


# Media (our own storage)
MEDIA_URL = "/media/"
MEDIA_ROOT = "/data/media"

# Small helper used by views to build safe paths
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}


def build_media_path(*parts):
    # prevent path traversal
    safe = [str(p).replace("..", "").lstrip("/") for p in parts]
    return os.path.join(MEDIA_ROOT, *safe)


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    # "DEFAULT_RENDERER_CLASSES": [
    #     "rest_framework.renderers.JSONRenderer",
    #     # Browsable API တင်ချင်ရင် အောက်က uncomment လုပ်
    #     # "rest_framework.renderers.BrowsableAPIRenderer",
    # ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # "DEFAULT_THROTTLE_CLASSES": [
    #     "rest_framework.throttling.AnonRateThrottle",
    #     "rest_framework.throttling.UserRateThrottle",
    #     "rest_framework.throttling.ScopedRateThrottle",
    # ],
    # "DEFAULT_THROTTLE_RATES": {
    #     "anon": "30/min",
    #     "user": "120/min",
    #     "session_join": "60/min",
    # },
}



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


USE_REDIS_CACHE = True
if USE_REDIS_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "KEY_PREFIX": "loxa",
        }
    }
else:
    # Option B: Database cache (no extra dependency)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "loxa_cache_table",
        }
    }


AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",   # add providers you need
    "django.contrib.auth.backends.ModelBackend",
)



# OAuth client keys via env
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("GOOGLE_CLIENT_ID","")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("GOOGLE_CLIENT_SECRET","")

# After social auth succeeds, we mint JWT:
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)


SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,  # we'll use Bearer JWT
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'Paste **Bearer &lt;your_JWT&gt;** here. Example: `Bearer eyJ0eXAiOiJK...`',
        },
    },
}