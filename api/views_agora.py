# api/views_agora.py
from rest_framework import permissions, views, status
from rest_framework.response import Response
from django.conf import settings
from .serializers_agora import AgoraTokenRequestSer, AgoraTokenResponseSer
from .agora_utils import build_rtc_token, build_rtm_token
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

class TokenThrottle(ScopedRateThrottle):
    scope = "session_join"
class AgoraTokenView(views.APIView):
    """
    GET/POST /api/agora/token/?channel=...&role=subscriber
    - Authenticated users only (so we know uid)
    """
    permission_classes = [permissions.IsAuthenticated]

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
        channel = ser.validated_data["channel"] # type: ignore
        role = ser.validated_data["role"] # type: ignore
        ttl = ser.validated_data.get("ttl") or settings.AGORA_TOKEN_TTL_SEC # type: ignore

        uid = str(request.user.id)  # you can switch to int if you enforce numeric
        rtc = build_rtc_token(channel, uid, role=role, ttl=ttl)
        rtm = build_rtm_token(uid, ttl=ttl)

        out = {
            "channel": channel,
            "uid": uid,
            "rtc_token": rtc,
            "rtm_token": rtm,
            "expires_in": int(ttl),
        }
        return Response(AgoraTokenResponseSer(out).data, status=status.HTTP_200_OK)


class AgoraViewSet (ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='token')
    def token(self, request):
        return Response({"token": "..."})
