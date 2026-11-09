import os
from pathlib import Path
from datetime import timedelta
from corsheaders.defaults import default_headers

# --- Basic Django Setup ---
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-development-key")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = _env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["lms.ai1.com.mm", "lms2.ai1.com.mm", "web", "localhost", "127.0.0.1", "10.0.2.2"],
)
ROOT_URLCONF = 'loxa.urls'
WSGI_APPLICATION = 'loxa.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

SITE_ID = 1 # Required by django-allauth

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = False
SECURE_PROXY_SSL_HEADER = None
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

CSRF_TRUSTED_ORIGINS = _env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [
        'https://lms.ai1.com.mm',
        'https://lms2.ai1.com.mm',
        'http://localhost',
        'http://127.0.0.1',
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:8080',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:8080',
    ],
)

# --- Custom User Models ---
AUTH_USER_MODEL = "accounts.User"
AUTH_ORG_MODEL = "accounts.Organization"


# --- Application Definitions ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third Party Apps
    "rest_framework",
    "rest_framework.authtoken", # ADDED TO FIX dj-rest-auth STARTUP ERROR
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_yasg",
    "django_filters",
    "django_prometheus",
    
    # Social authentication
    # 'social_django',
    
    # Allauth for social login
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # dj-rest-auth for API endpoints
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Your Apps
    "api",
    "orgs",
    "accounts",
    "authphone",
]


# --- Middleware Configuration ---
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "loxa.middleware.TenantResolver",
    "orgs.middleware.CurrentOrgMiddleware",
    "allauth.account.middleware.AccountMiddleware", # Added for allauth
]


# --- Template Configuration ---
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


# --- Database Configuration ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "loxa_db"),
        "USER": os.getenv("POSTGRES_USER", "loxa_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "loxa@loxa"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# --- Authentication Configuration ---
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
    # Social auth backend
    # 'social_core.backends.google.GoogleOAuth2',
    # Custom phone backend
    "authphone.backends.PhoneBackend",
]

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Static and Media Files ---
STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", "/data/static")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/data/media")
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}


# --- REST Framework and JWT Configuration ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_THROTTLE_RATES": {
        "otp_request": os.getenv("THROTTLE_OTP_REQUEST", "10/hour"),
        "otp_verify": os.getenv("THROTTLE_OTP_VERIFY", "20/hour"),
        "agora_token": os.getenv("THROTTLE_AGORA_TOKEN", "120/hour"),
        "session_join": os.getenv("THROTTLE_SESSION_JOIN", "120/hour"),
    },
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
REST_AUTH = {
    'USE_JWT': True,
    'SIGNUP_FIELDS': {
        'username': {'required': False},
        'email': {'required': True},
    },
    'JWT_AUTH_HTTPONLY': False,
    'SESSION_LOGIN': False, # Disable session login for API
}


# --- django-allauth Configuration ---
# Fixes the 'User has no field named username' error
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_METHODS = {'email'} 
# ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none' # Set to 'mandatory' in production if desired

ACCOUNT_SIGNUP_FIELDS = [
    'email*', 
    'password1',  # ပထမ password field
    'password2',  # အတည်ပြုရန် password field
    # 'first_name', # လိုအပ်ပါက ထည့်ပါ
]

# THIS IS THE FIX: Skip the confirmation page and go directly to Google
SOCIALACCOUNT_LOGIN_ON_GET = True

# Default redirect URL after successful login
# 🛑 FIX: Login ပြီးနောက် Flutter dashboard သို့ redirect လုပ်ရန် URL ကို သတ်မှတ်ပါ။
# LOGIN_REDIRECT_URL = 'https://lms.myanmarlink.online/student/dashboard'
LOGIN_REDIRECT_URL = 'http://localhost:8000/api/'

# Force HTTPS for OAuth redirects
if not DEBUG:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' # 🛑 FIX: Production အတွက် HTTPS ကို သုံးပါ။
    SOCIALACCOUNT_QUERY_EMAIL = True
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'APP': {
#             'client_id': os.getenv('GOOGLE_CLIENT_ID'),
#             'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
#             'key': ''
#         },
#         'SCOPE': ['profile', 'email'],
#         'AUTH_PARAMS': {'access_type': 'online'},
#         'VERIFIED_EMAIL': True,
#     }
# }

if not DEBUG:
    SITE_URL = os.getenv("SITE_URL", "https://lms.ai1.com.mm/")
else:
    SITE_URL = os.getenv("SITE_URL", "http://localhost:8000/")

# Social Auth Configuration (for social-auth-app-django)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['openid', 'email', 'profile']
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['username', 'first_name', 'last_name']


# --- CORS Configuration ---
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL_ORIGINS", True)
else:
    CORS_ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL_ORIGINS", False)
    CORS_ALLOWED_ORIGINS = _env_list(
        "CORS_ALLOWED_ORIGINS",
        [
            "https://lms.ai1.com.mm",
            "https://lms2.ai1.com.mm",
            "https://lms.myanmarlink.online",
        ],
    )
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-org-id",
    "x-org-id".upper(),
]

# --- Production Security Settings ---
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", True)

    # Session security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

USE_HTTPS = _env_bool("USE_HTTPS", not DEBUG)

# --- Other Service Configurations (Redis, Celery, Agora, Sentry, etc.) ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

AGORA_APP_ID = os.getenv("AGORA_APP_ID", "")
AGORA_APP_CERT = os.getenv("AGORA_APP_CERT", "")
AGORA_TOKEN_TTL_SEC = int(os.getenv("AGORA_TOKEN_TTL_SEC", "3600"))
AGORA_REQUIRE_CREDENTIALS = _env_bool("AGORA_REQUIRE_CREDENTIALS", not DEBUG)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )





EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mailhog'         # <--- Docker service name
EMAIL_PORT = 1025              # <--- Mailhog ရဲ့ SMTP port
EMAIL_HOST_USER = ''           # Mailhog မှာ မလိုပါ
EMAIL_HOST_PASSWORD = ''       # Mailhog မှာ မလိုပါ


SOCIALACCOUNT_ADAPTER = 'accounts.adapter.CustomSocialAccountAdapter'
