# api/views_agora.py
from django.conf import settings
from rest_framework import permissions, status, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ViewSet

from .agora_utils import build_rtc_token, build_rtm_token
from .serializers_agora import AgoraTokenRequestSer, AgoraTokenResponseSer


class TokenThrottle(ScopedRateThrottle):
    scope = "agora_token"


class AgoraTokenView(views.APIView):
    """
    GET/POST /api/agora/token/?channel=...&role=subscriber
    - Authenticated users only (so we know uid)
    Flutter-friendly: includes app_id, expires_in, expire_at, token/rtc_token.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [TokenThrottle]

    def post(self, request):
        return self._issue(request)

    def get(self, request):
        return self._issue(request)

    def _issue(self, request):
        data = {
            "channel": request.query_params.get("channel") or request.data.get("channel"),
            "role": request.query_params.get("role") or request.data.get("role") or "subscriber",
            "ttl": request.query_params.get("ttl") or request.data.get("ttl"),
        }
        ser = AgoraTokenRequestSer(data=data)
        ser.is_valid(raise_exception=True)
        channel = ser.validated_data["channel"]  # type: ignore
        role = ser.validated_data["role"]  # type: ignore
        ttl = int(ser.validated_data.get("ttl") or settings.AGORA_TOKEN_TTL_SEC)  # type: ignore

        app_id = getattr(settings, "AGORA_APP_ID", "")
        app_cert = getattr(settings, "AGORA_APP_CERT", "")
        require = getattr(settings, "AGORA_REQUIRE_CREDENTIALS", not settings.DEBUG)
        if require and not (app_id and app_cert):
            return Response(
                {"detail": "agora credentials not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not (app_id and app_cert):
            return Response({"detail": "agora creds missing"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        uid = str(request.user.id)
        rtc = build_rtc_token(channel, uid, role=role, ttl=ttl)
        rtm = build_rtm_token(uid, ttl=ttl)
        expire_at = int(__import__("time").time()) + ttl

        out = {
            "app_id": app_id,
            "channel": channel,
            "uid": uid,
            "token": rtc,
            "rtc_token": rtc,
            "rtm_token": rtm,
            "role": role,
            "expires_in": ttl,
            "expire_at": expire_at,
        }
        return Response(AgoraTokenResponseSer(out).data, status=status.HTTP_200_OK)


class AgoraViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TokenThrottle]

    @action(detail=False, methods=["post"], url_path="token")
    def token(self, request):
        # Delegate to the canonical implementation.
        return AgoraTokenView()._issue(request)
