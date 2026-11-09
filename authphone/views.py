from rest_framework import permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import MeSerializer

from .models import PhoneOTP
from .serializers import RequestOTPSerializer, VerifyOTPSerializer
from .services import generate_otp, get_sms_backend


class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp_request"  # configure in DRF settings

    def post(self, request):
        ser = RequestOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"]  # type: ignore

        code = generate_otp(6)
        otp = PhoneOTP.create_for(phone, code, ttl_sec=300)

        backend = get_sms_backend()
        sms = backend.send(phone, f"Your verification code is {code}")

        return Response({"ok": sms.ok, "expires_at": otp.expires_at})


class VerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp_verify"

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone, code = ser.validated_data["phone"], ser.validated_data["code"]  # type: ignore

        otp = (
            PhoneOTP.objects.filter(phone=phone)
            .order_by("-created_at")
            .first()
        )
        if not otp or not otp.verify(code):
            return Response({"detail": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

        User = __import__("django.contrib.auth").contrib.auth.get_user_model()
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            user = User.objects.create(phone_number=phone, email=f"{phone}@local.invalid", is_active=True)
        # store verified state on OTP/user if fields exist
        if hasattr(user, "is_phone_verified"):
            try:
                user.is_phone_verified = True  # type: ignore[attr-defined]
                user.save(update_fields=["is_phone_verified"])
            except Exception:
                pass
        otp.user = user
        try:
            otp.save(update_fields=["user"])
        except Exception:
            pass

        refresh = RefreshToken.for_user(user)
        payload = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user, context={"request": request}).data,
        }
        org = getattr(request, "org", None)
        payload["org"] = {"id": getattr(org, "id", None), "name": getattr(org, "name", None)} if org else None
        return Response(payload)
