from django.conf import settings
from time import time
try:
    from agora_token_builder import RtcTokenBuilder, RtmTokenBuilder
except Exception:
    RtcTokenBuilder = None
    RtmTokenBuilder = None

def build_rtc_token(channel: str, uid: int | str, role: str = "publisher", ttl: int | None = None) -> str:
    """
    role: "publisher" (host/teacher) or "subscriber" (student)
    """
    app_id = settings.AGORA_APP_ID
    app_cert = settings.AGORA_APP_CERT
    ttl = ttl or settings.AGORA_TOKEN_TTL_SEC
    if not (RtcTokenBuilder and app_id and app_cert):
        # Dev fallback (DON'T use in prod)
        return f"DUMMY_RTC_{channel}_{uid}"
    # role: 1 = PUBLISHER, 2 = SUBSCRIBER
    agora_role = 1 if role.lower() == "publisher" else 2
    expire_ts = int(time()) + int(ttl) # type: ignore
    # Agora SDK expects numeric uid (0 allowed). If string, force int or 0.
    try:
        agora_uid = int(uid)
    except Exception:
        agora_uid = 0
    return RtcTokenBuilder.buildTokenWithUid(app_id, app_cert, channel, agora_uid, agora_role, expire_ts)

def build_rtm_token(uid: str | int, ttl: int | None = None) -> str:
    app_id = settings.AGORA_APP_ID
    app_cert = settings.AGORA_APP_CERT
    ttl = ttl or settings.AGORA_TOKEN_TTL_SEC
    if not (RtmTokenBuilder and app_id and app_cert):
        return f"DUMMY_RTM_{uid}"
    expire_ts = int(time()) + int(ttl) # type: ignore
    return RtmTokenBuilder.buildToken(app_id, app_cert, str(uid), expire_ts) # type: ignore
