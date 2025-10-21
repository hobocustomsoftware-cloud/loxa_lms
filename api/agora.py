# api/views/agora.py
import time, os
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from agora_token_builder import RtcTokenBuilder
from django.conf import settings

@login_required
@require_GET
def rtc_token(request):
    app_id = settings.AGORА_APP_ID if hasattr(settings, "AGORА_APP_ID") else settings.AGORA_APP_ID
    app_cert = settings.AGORА_APP_CERT if hasattr(settings, "AGORА_APP_CERT") else settings.AGORA_APP_CERT
    if not app_id or not app_cert:
        return HttpResponseForbidden("Agora credentials missing")

    channel = request.GET.get("channel")
    uid = int(request.GET.get("uid", "0") or 0)   # mobile clients use int uid
    role_str = (request.GET.get("role") or "audience").lower()

    if not channel:
        return HttpResponseBadRequest("channel required")

    # ✅ သင့် permission စစ်ချက် (ဥပမာ: host/instructor သာ publish လုပ်ခွင့်)
    is_host = role_str in ("host", "publisher")
    if is_host and not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("not allowed to publish")

    # ထိုက်တန်သလို course enrollment / channel ownership စစ်ပြီးမှ ထုတ်ချင်ရင် ဒီနေရာထဲရေး
    # e.g. check_user_can_join_channel(request.user, channel)

    expire_seconds = 60 * 60  # 1 hour
    now = int(time.time())
    expire_at = now + expire_seconds

    role = Role_Publisher if is_host else Role_Subscriber # type: ignore
    token = RtcTokenBuilder.build_token_with_uid( # type: ignore
        app_id, app_cert, channel, uid, role, expire_at
    )
    return JsonResponse({"token": token, "expire_at": expire_at})
