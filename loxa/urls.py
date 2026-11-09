"""
URL configuration for loxa project. (Simplified)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from django.db import connection

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from api import social_views



# --- Social Authentication Views ---
from dj_rest_auth.registration.views import SocialLoginView, SocialConnectView  # type: ignore
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter # type: ignore
from allauth.socialaccount.providers.oauth2.client import OAuth2Client  # type: ignore


# Custom View Classes for API Login/Connect
class GoogleLogin(SocialLoginView):
    # Google Login ကို စတင်ရန်အတွက် /api/auth/google/ မှာ အသုံးပြုမည်
    adapter_class = GoogleOAuth2Adapter

class GoogleConnect(SocialConnectView):
    # ရှိပြီးသားအကောင့်နဲ့ ချိတ်ဆက်ရန်အတွက် အသုံးပြုမည်
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

def root_status(request):
    return JsonResponse({"status": "API Root - Login Successful", "user": str(request.user)})



# --- Helper Views for Health Checks ---
def live(_): return JsonResponse({"ok": True})
def ready(_):
    try:
        with connection.cursor() as c: c.execute("SELECT 1")
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "err": str(e)}, status=500)




# --- Swagger/OpenAPI Schema View ---
schema_view = get_schema_view(
    openapi.Info(
        title="Loxa API",
        default_version="v1",
        description="Online live classroom API",
        contact=openapi.Contact(email="support@loxa.local"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


# --- Main URL Patterns ---
urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # 🛑 1. ALLAUTH DEFAULT CALLBACK URLS (Google က ပြန်ပို့မည့် လမ်းကြောင်းများ)
    # Google Console တွင် http://localhost:8000/accounts/google/login/callback/ ကို သုံးရန်
    path('accounts/', include('allauth.urls')), 

    # --- API Block ---
    path("api/", include("api.urls")),
    path("api/accounts/", include("accounts.urls")), 
    path("api/auth/phone/", include("authphone.urls")),

    # JWT token endpoints (Flutter/mobile canonical)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # dj-rest-auth endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # Google mobile/SPA token exchange (canonical for Flutter)
    path('api/auth/google/mobile/', social_views.GoogleMobileAuthView.as_view(), name='google_mobile_auth'),
    path('api/auth/google/code/', social_views.GoogleExchangeView.as_view(), name='google_code_exchange'),
    path('api/auth/google/url/', social_views.GoogleAuthUrlView.as_view(), name='google_auth_url'),
    
    # dj-rest-auth social login/connect (web/API compatibility)
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/google/connect/', GoogleConnect.as_view(), name='google_connect'), 
    
     # --- Utility and Documentation URLs ---
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("health/live/", live),
    path("health/ready/", ready),
    path("", include("django_prometheus.urls")),
    path('', root_status, name='api_root'),
]

# Serve media files only when in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)