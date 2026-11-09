# api/social_views.py
import requests
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_backend, load_strategy

from accounts.serializers import MeSerializer

User = get_user_model()

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _jwt_for(user):
    rf = RefreshToken.for_user(user)
    return {"access": str(rf.access_token), "refresh": str(rf)}


def _auth_payload(request, user):
    payload = _jwt_for(user)
    payload["user"] = MeSerializer(user, context={"request": request}).data
    org = getattr(request, "org", None)
    payload["org"] = (
        {"id": getattr(org, "id", None), "name": getattr(org, "name", None)} if org else None
    )
    return payload


def _default_redirect_uri(request):
    if settings.DEBUG:
        return request.build_absolute_uri("/auth/google/callback")
    return getattr(settings, "SITE_URL", "https://lms.ai1.com.mm/").rstrip("/") + "/auth/google/callback"


def _get_or_create_google_user(
    email: str, name: str | None = None, given_name: str | None = None, family_name: str | None = None
):
    if not email:
        return None
    defaults = {
        "first_name": (given_name or (name or "").split(" ")[0] or email.split("@")[0])[:150],
        "last_name": (family_name or " ".join((name or "").split(" ")[1:]))[:150],
        "is_active": True,
    }
    user, created = User.objects.get_or_create(email=email.lower(), defaults=defaults)
    if created and hasattr(user, "add_role"):
        try:
            user.add_role("student")
        except Exception:
            pass
    changed = False
    if defaults["first_name"] and not getattr(user, "first_name", ""):
        user.first_name = defaults["first_name"]
        changed = True
    if defaults["last_name"] and not getattr(user, "last_name", ""):
        user.last_name = defaults["last_name"]
        changed = True
    if changed:
        user.save(update_fields=["first_name", "last_name"])
    return user


class GoogleMobileInSer(serializers.Serializer):
    id_token = serializers.CharField(
        required=False, help_text="Google ID token from native/mobile sign-in"
    )
    access_token = serializers.CharField(
        required=False, help_text="Google access token (fallback)"
    )
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get("id_token") and not attrs.get("access_token"):
            raise serializers.ValidationError("id_token or access_token is required")
        return attrs


class GoogleMobileAuthView(APIView):
    """
    Canonical Flutter/mobile Google sign-in.
    POST {"id_token":"..."} or {"access_token":"..."} -> JWT + user profile.
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Google mobile sign-in (id_token/access_token -> JWT)",
        request_body=GoogleMobileInSer,
    )
    def post(self, request):
        ser = GoogleMobileInSer(data=request.data)
        ser.is_valid(raise_exception=True)
        id_tok = ser.validated_data.get("id_token")
        access_token = ser.validated_data.get("access_token")
        email_hint = (ser.validated_data.get("email") or "").lower()

        info = {}
        client_id = getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "") or getattr(
            settings, "GOOGLE_CLIENT_ID", ""
        )
        if id_tok:
            try:
                req = google_requests.Request()
                info = google_id_token.verify_oauth2_token(id_tok, req, audience=client_id or None)
            except Exception as e:
                if settings.DEBUG:
                    info = {"_verify_error": str(e)}
                else:
                    info = {}
        if not info.get("email") and access_token:
            try:
                ures = requests.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=15,
                )
                if ures.status_code == 200:
                    info = {**info, **ures.json()}
            except Exception:
                pass
        if not info.get("email") and email_hint and settings.DEBUG:
            info["email"] = email_hint
            info["name"] = email_hint.split("@")[0]

        email = (info.get("email") or "").lower()
        if not email:
            return Response(
                {"detail": "Unable to verify Google token or determine email"}, status=400
            )
        user = _get_or_create_google_user(
            email=email,
            name=info.get("name"),
            given_name=info.get("given_name"),
            family_name=info.get("family_name"),
        )
        if not user or not user.is_active:
            return Response({"detail": "User is inactive"}, status=403)
        return Response(_auth_payload(request, user), status=200)


class SocialAuthExchangeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")
        if not provider or not access_token:
            return Response({"detail": "provider/access_token required"}, status=400)
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name=provider, redirect_uri=None)
        user = backend.do_auth(access_token)
        if not user or not user.is_active:
            return Response({"detail": "invalid social token"}, status=400)
        return Response(_auth_payload(request, user))


class GoogleAuthUrlSer(serializers.Serializer):
    auth_url = serializers.URLField()
    redirect_uri_used = serializers.CharField(required=False)
    client_id = serializers.CharField(required=False)


class GoogleExchangeInSer(serializers.Serializer):
    code = serializers.CharField(help_text="Authorization code from Google redirect")
    redirect_uri = serializers.URLField(help_text="Must match the one used to open the Google consent page")


class JWTOutSer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField(required=False)
    org = serializers.DictField(required=False, allow_null=True)


class GoogleAuthUrlView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Get Google OAuth consent URL", responses={200: GoogleAuthUrlSer})
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
        return Response({"auth_url": url, "redirect_uri_used": redirect_uri, "client_id": client_id})


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
        code = ser.validated_data["code"]
        redirect_uri = ser.validated_data["redirect_uri"]
        data = {
            "code": code,
            "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        tok = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
        if tok.status_code != 200:
            return Response(
                {"detail": "token exchange failed", "raw": tok.text if settings.DEBUG else ""},
                status=400,
            )
        tokens = tok.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return Response({"detail": "no access_token in response"}, status=400)
        ures = requests.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15
        )
        if ures.status_code != 200:
            return Response({"detail": "userinfo fetch failed"}, status=400)
        ui = ures.json()
        email = (ui.get("email") or "").lower()
        if not email:
            return Response({"detail": "No email from Google"}, status=400)
        user = _get_or_create_google_user(
            email=email, name=ui.get("name"), given_name=ui.get("given_name"), family_name=ui.get("family_name")
        )
        return Response(_auth_payload(request, user), status=200)


class GoogleRedirectDebugView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

        adapter = GoogleOAuth2Adapter(request)
        redirect_uri = adapter.get_callback_url(request, None)
        custom_redirect_uri = _default_redirect_uri(request)
        return Response(
            {
                "allauth_redirect_uri": redirect_uri,
                "custom_redirect_uri": custom_redirect_uri,
                "request_host": request.get_host(),
                "request_scheme": request.scheme,
                "debug_mode": settings.DEBUG,
                "site_url": getattr(settings, "SITE_URL", "Not set"),
                "google_client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            }
        )
