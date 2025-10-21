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

    # 🛑 2. DJ-REST-AUTH: Authentication Endpoints
    # /api/auth/login/, /api/auth/logout/, /api/auth/registration/ များကို ထောက်ပံ့သည်
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # 🛑 3. GOOGLE SOCIAL LOGIN ENDPOINT (Frontend ကနေ စခေါ်မယ့်နေရာ)
    # /api/auth/google/ ဖြင့် Login Flow ကို စတင်မည်
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),

    # 4. GOOGLE CONNECT ENDPOINT (အကောင့်ချိတ်ဆက်ရန်)
    # Connect ကို api/auth/google/connect/ လိုမျိုး အနေအထားမှာ ထားသင့်ပါသည်။
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