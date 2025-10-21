from rest_framework import status, permissions, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model, login
from django.utils import timezone

from .models import PhoneOTP
from .serializers import RequestOTPSerializer, VerifyOTPSerializer
from .services import get_sms_backend, generate_otp

User = get_user_model()

class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp_request"  # enable in DRF settings

    def post(self, request):
        ser = RequestOTPSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = ser.validated_data["phone"] # type: ignore

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
        phone, code = ser.validated_data["phone"], ser.validated_data["code"] # type: ignore

        otp = (PhoneOTP.objects
            .filter(phone=phone)
            .order_by("-created_at")
            .first())
        if not otp or not otp.verify(code):
            return Response({"detail":"Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

        # create or get user
        user, _ = User.objects.get_or_create(phone_number=phone, defaults={"email": f"{phone}@local"})
        user.is_phone_verified = True # type: ignore
        user.save(update_fields=["is_phone_verified"])

        # (a) Session login
        login(request, user)

        # (b) or Return JWT (if SimpleJWT on)
        # from rest_framework_simplejwt.tokens import RefreshToken
        # refresh = RefreshToken.for_user(user)
        # return Response({"access": str(refresh.access_token), "refresh": str(refresh)})

        return Response({"ok": True, "user_id": user.id}) # type: ignore
