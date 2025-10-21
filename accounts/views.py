from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import MeSerializer
from .serializers import PhoneRegisterSerializer, PhoneLoginSerializer, User
from django.contrib.auth import get_user_model


# User = get_user_model()


class PhoneRegisterView(generics.CreateAPIView):
    serializer_class = PhoneRegisterSerializer
    queryset = User.objects.all()


class PhoneLoginView(generics.GenericAPIView):
    serializer_class = PhoneLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        user = authenticate(request, phone_number=phone_number, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "phone_number": user.phone_number,
        })




# class RequestOTPView(generics.GenericAPIView):
#     serializer_class = RequestOTPSerializer

#     def post(self, request, *args, **kwargs):
#         ser = self.get_serializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         ser.save()
#         return Response({"detail": "OTP sent"}, status=status.HTTP_200_OK)


# class VerifyOTPView(generics.GenericAPIView):
#     serializer_class = VerifyOTPSerializer

#     def post(self, request, *args, **kwargs):
#         ser = self.get_serializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         token_data = ser.save()
#         return Response(token_data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(MeSerializer(request.user).data)