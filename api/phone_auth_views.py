# api/phone_auth_views.py
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from .models_auth import PhoneOTP
from rest_framework.permissions import BasePermission


User = get_user_model()

def send_sms(phone: str, message: str):
    # DEV: print to console; PROD: integrate your GSM modem/SMPP HTTP gateway
    print(f"[SMS] to={phone} msg={message}")

class OTPSendThrottle(ScopedRateThrottle):
    scope = "otp_send"

class OTPVerifyThrottle(ScopedRateThrottle):
    scope = "otp_verify"

class SendPhoneOTP(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPSendThrottle]

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"detail":"phone required"}, status=400)
        code = f"{random.randint(0,999999):06d}"
        otp = PhoneOTP.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        send_sms(phone, f"Your Loxa code is {code}. Expires in 5 minutes.")
        return Response({"session_id": str(otp.session_id)})

class VerifyPhoneOTP(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        phone = request.data.get("phone")
        session_id = request.data.get("session_id")
        code = request.data.get("code")
        if not (phone and session_id and code):
            return Response({"detail":"phone, session_id, code required"}, status=400)
        try:
            otp = PhoneOTP.objects.filter(phone=phone, session_id=session_id).latest("created_at")
        except PhoneOTP.DoesNotExist:
            return Response({"detail":"invalid session"}, status=400)

        if otp.expired():
            return Response({"detail":"code expired"}, status=400)
        if otp.attempts >= 5:
            return Response({"detail":"too many attempts"}, status=429)

        otp.attempts += 1
        otp.save(update_fields=["attempts"])

        if otp.code != code:
            return Response({"detail":"invalid code"}, status=400)

        # success: get or create user; you can store phone in user model
        user, _ = User.objects.get_or_create(username=f"phone_{phone}", defaults={"email": ""})
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })



class IsOrgMember(BasePermission):
    message = "Not a member of this org."

    def has_permission(self, request, view):
        org = getattr(request, "org", None)
        if not org:
            return False
        # JWT claims
        org_ids = (request.auth or {}).get("org_ids") if hasattr(request, "auth") else None
        if isinstance(org_ids, list) and org.id in org_ids:
            return True
        # fallback DB check (session auth)
        user = request.user
        if user.is_authenticated and hasattr(user, "memberships"):
            return user.memberships.filter(org=org).exists()
        return False