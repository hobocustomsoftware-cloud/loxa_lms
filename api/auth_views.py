# api/auth_views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .auth_serializers import LoxaTokenObtainPairSerializer

from django.contrib.auth import authenticate, login, get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser


class LoxaTokenView(TokenObtainPairView):
    serializer_class = LoxaTokenObtainPairSerializer



class SessionLoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]  # ✅ accept JSON & form

    def post(self, request):
        data = request.data  # will work for JSON or form
        identifier = data.get("identifier") or data.get("username") or data.get("email")
        password   = data.get("password")

        if not identifier or not password:
            # (သေချာစစ်ဖို့ dev only) what arrived?
            return Response(
                {"detail": "username/email and password are required", "received": data},
                status=400,
            )

        User = get_user_model()
        username_field = getattr(User, "USERNAME_FIELD", "username")

        # 1) try directly with your USERNAME_FIELD
        creds = {username_field: identifier, "password": password}
        user = authenticate(request, **creds)

        # 2) fallback if identifier is email but USERNAME_FIELD != 'email'
        if user is None and "@" in identifier and username_field != "email":
            try:
                account = User.objects.get(email__iexact=identifier)
                creds = {username_field: getattr(account, username_field), "password": password}
                user = authenticate(request, **creds)
            except User.DoesNotExist:
                pass

        if not user:
            return Response({"detail": "invalid credentials"}, status=400)
        if getattr(user, "is_active", True) is False:
            return Response({"detail": "inactive account"}, status=403)

        login(request, user)  # ➜ Set-Cookie: sessionid
        return Response({"ok": True, "user_id": user.pk}, status=200)