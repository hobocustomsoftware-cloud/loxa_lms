from gettext import install
import os
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models_academics import Lesson, LessonAsset, Module
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LiveSession, SeatReservation, Attendance
from .serializers import LiveSessionSerializer, JoinResponseSer, LeaveResponseSer
from rest_framework.decorators import action
from rest_framework.response import Response



AGORA_APP_ID = os.getenv("AGORA_APP_ID", "")
AGORA_APP_CERT = os.getenv("AGORA_APP_CERT", "")

Optional: install agora_token_builder==1.0.0 # type: ignore
try:
    from agora_token_builder import RtcTokenBuilder # type: ignore
except Exception:
    RtcTokenBuilder = None



class OrgScopedMixin:
    def get_queryset(self):
        qs = super().get_queryset() # type: ignore
        org = getattr(self.request, "org", None) # type: ignore
        return qs.filter(org=org) if org else qs.none()


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: LiveSession):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id == request.user.id # type: ignore


# class LiveSessionViewSet(viewsets.ModelViewSet):
#     queryset = LiveSession.objects.all().select_related("owner")
#     serializer_class = LiveSessionSerializer        # <<— CRITICAL LINE
#     permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
#     throttle_scope = "session_join"

    # @action(detail=True, methods=["post"])
    # def join(self, request, pk=None):
    #     user = request.user
    #     session = self.get_object()
    #     org = getattr(request, "org", getattr(session, "org", None))

    #     with transaction.atomic():
    #         current = (SeatReservation.objects
    #             .select_for_update()
    #             .filter(session=session, state__in=["PENDING", "CONFIRMED"])
    #             .count()
    #         )
    #         if current >= session.max_participants:
    #             return Response({"detail": "Room full"}, status=status.HTTP_409_CONFLICT)

    #         SeatReservation.objects.update_or_create(
    #             org=org, session=session, user=user,
    #             defaults={
    #                 "state": "CONFIRMED",
    #                 "expires_at": timezone.now() + timedelta(minutes=5)
    #             },
    #         )

    #         Attendance.objects.get_or_create(org=org, session=session, user=user)

    #     expires_at = timezone.now() + timedelta(minutes=session.duration_minutes + 15)
    #     uid = str(user.id)
    #     channel = session.channel_name

    #     if RtcTokenBuilder and AGORA_APP_ID and AGORA_APP_CERT:
    #         from time import time as now
    #         privilege_expired_ts = int(now()) + (session.duration_minutes + 15) * 60
    #         try:
    #             rtc_token = RtcTokenBuilder.buildTokenWithUid(
    #                 AGORA_APP_ID, AGORA_APP_CERT, channel, int(user.id), 1, privilege_expired_ts
    #             )
    #         except Exception:
    #             rtc_token = f"DUMMY_{channel}_{uid}"
    #     else:
    #         rtc_token = f"DUMMY_{channel}_{uid}"

    #     payload = {"channel": channel, "uid": uid, "rtc_token": rtc_token, "expires_at": expires_at}
    #     return Response(JoinResponseSer(payload).data, status=status.HTTP_200_OK)

    # @action(detail=True, methods=["post"])
    # def leave(self, request, pk=None):
    #     user = request.user
    #     session = self.get_object()

    #     with transaction.atomic():
    #         try:
    #             att = Attendance.objects.select_for_update().get(session=session, user=user)
    #         except Attendance.DoesNotExist:
    #             return Response({"detail": "not joined"}, status=status.HTTP_400_BAD_REQUEST)

    #         if not att.left_at:
    #             att.left_at = timezone.now()
    #             delta = (att.left_at - att.joined_at).total_seconds()
    #             if delta > 0:
    #                 att.total_seconds = int(delta)
    #             att.save(update_fields=["left_at", "total_seconds"])

    #         SeatReservation.objects.filter(session=session, user=user).update(state="RELEASEED")

    #     return Response(LeaveResponseSer({"ok": True}).data)

    # @action(detail=True, methods=["post"], url_path="recording/init")
    # def recording_init(self, request, pk=None):
    #     """
    #     Session နဲ့ ဆက်စပ် Lesson တစ်ခု မရှိသေးရင် create လုပ် → RECORDING asset တစ်ခုဆောက်
    #     ပြီး upload/play endpoint ပြန်ပေး
    #     body: { "title": "Class A - 2025-09-03" }
    #     """
    #     org = getattr(request, "org", None)
    #     session = self.get_object()

    #     # (1) Module ရှိမှ Lesson မဖြစ်နိုင် → guard
    #     module = Module.objects.filter(org=org).order_by("id").first() if org else Module.objects.order_by("id").first()
    #     if not module:
    #         return Response({"detail": "Please create a Module first."}, status=status.HTTP_400_BAD_REQUEST)

    #     # (2) Lesson upsert (session-link)
    #     lesson, _ = Lesson.objects.get_or_create(
    #         org=org, live_session=session,
    #         defaults={
    #             "module": module,
    #             "title": request.data.get("title", session.title),
    #             "order": 0,
    #         },
    #     )

    #     # (3) Asset create (LessonAsset model ထဲမှာ title field မရှိရင် မပို့ပါ!)
    #     asset = LessonAsset.objects.create(
    #         org=org, lesson=lesson, type="RECORDING", storage_key=""  # storage_key ကို နောက်ထပ်ဖြည့်
    #     )

    #     # storage_key ကို deterministic အဖြစ် တည်ဆောက်
    #     rel = f"org/{getattr(org,'id','_')}/lesson/{lesson.id}/asset/{asset.id}/source.mp4"
    #     asset.storage_key = rel
    #     asset.save(update_fields=["storage_key"])

    #     return Response({
    #         "asset_id": asset.id,
    #         "upload_endpoint": f"/api/assets/{asset.id}/upload/",
    #         "play_endpoint": f"/api/assets/{asset.id}/play/"
    #     }, status=status.HTTP_200_OK)



from rest_framework.throttling import ScopedRateThrottle
class OrgScopedThrottle(ScopedRateThrottle):
    def get_cache_key(self, request, view):
        base = super().get_cache_key(request, view)
        org = getattr(request, "org", None)
        if base and org:
            return f"{base}:org:{org.id}"
        return base
