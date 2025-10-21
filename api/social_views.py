# api/social_views.py
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from social_django.utils import load_strategy, load_backend
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from urllib.parse import urlencode
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class SocialAuthExchangeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        provider = request.data.get("provider")   # "google-oauth2"
        access_token = request.data.get("access_token")
        if not provider or not access_token:
            return Response({"detail":"provider/access_token required"}, status=400)

        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name=provider, redirect_uri=None)
        user = backend.do_auth(access_token)
        if not user or not user.is_active:
            return Response({"detail":"invalid social token"}, status=400)

        login(request, user)  # optional
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })



class GoogleAuthUrlSer(serializers.Serializer):
    auth_url = serializers.URLField()

class GoogleExchangeInSer(serializers.Serializer):
    code = serializers.CharField(help_text="Authorization code from Google redirect")
    redirect_uri = serializers.URLField(help_text="Must match the one used to open the Google consent page")

class JWTOutSer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

def _jwt_for(user):
    rf = RefreshToken.for_user(user)
    return {"access": str(rf.access_token), "refresh": str(rf)}

def _default_redirect_uri(request):
    # frontend local dev URL or your hosted callback
    # Note: Google console မှာ authorized redirect URI အဖြစ် ဒီ URL ကို စာရင်းသွင်းထားရပါမယ်
    if settings.DEBUG:
        return request.build_absolute_uri("/auth/google/callback")
    else:
        # Force HTTPS for production
        return "https://lms.myanmarlink.online/auth/google/callback"

class GoogleAuthUrlView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get Google OAuth consent URL",
        responses={200: GoogleAuthUrlSer},
        manual_parameters=[
            openapi.Parameter(
                "redirect_uri", openapi.IN_QUERY, type=openapi.TYPE_STRING,
                description="Optional override. Must be whitelisted in Google console."
            ),
        ],
    )
    def get(self, request):
        client_id = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        redirect_uri = request.query_params.get("redirect_uri") or _default_redirect_uri(request)
        scope = "openid email profile"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "scope": scope,
        }
        url = f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"
        
        # Debug information
        debug_info = {
            "auth_url": url,
            "redirect_uri_used": redirect_uri,
            "client_id": client_id,
            "debug_mode": settings.DEBUG,
            "site_url": getattr(settings, 'SITE_URL', 'Not set'),
        }
        return Response(debug_info)



class GoogleExchangeView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Exchange Google code for JWT",
        request_body=GoogleExchangeInSer,
        responses={200: JWTOutSer, 400: "Bad Request"},
    )
    def post(self, request):
        ser = GoogleExchangeInSer(data=request.data)
        ser.is_valid(raise_exception=True)
        code = ser.validated_data["code"] # type: ignore
        redirect_uri = ser.validated_data["redirect_uri"] # type: ignore

        data = {
            "code": code,
            "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        tok = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        if tok.status_code != 200:
            return Response({"detail": "token exchange failed", "raw": tok.text}, status=400)

        tokens = tok.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return Response({"detail": "no access_token in response"}, status=400)

        # Fetch userinfo
        ures = requests.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
        if ures.status_code != 200:
            return Response({"detail": "userinfo fetch failed", "raw": ures.text}, status=400)

        ui = ures.json()
        email = ui.get("email")
        sub = ui.get("sub")
        name = ui.get("name") or email

        if not email:
            return Response({"detail": "No email from Google"}, status=400)

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0], "first_name": name}
        )
        jwt = _jwt_for(user)
        return Response(jwt, status=200)


class GoogleRedirectDebugView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Debug view to check what redirect URIs are being generated"""
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
        from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
        
        # Get the redirect URI that allauth would use
        adapter = GoogleOAuth2Adapter(request)
        redirect_uri = adapter.get_callback_url(request, None)
        
        # Get the redirect URI from our custom view
        custom_redirect_uri = _default_redirect_uri(request)
        
        debug_info = {
            "allauth_redirect_uri": redirect_uri,
            "custom_redirect_uri": custom_redirect_uri,
            "request_host": request.get_host(),
            "request_scheme": request.scheme,
            "request_meta_host": request.META.get('HTTP_HOST'),
            "request_meta_scheme": request.META.get('HTTP_X_FORWARDED_PROTO', request.scheme),
            "debug_mode": settings.DEBUG,
            "site_url": getattr(settings, 'SITE_URL', 'Not set'),
            "google_client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        }
        
        return Response(debug_info)