# api/google_auth_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests
import json

User = get_user_model()

class GoogleTokenSerializer(serializers.Serializer):
    """Serializer for Google ID token"""
    id_token = serializers.CharField(help_text="Google ID token from Google Sign-In")
    email = serializers.EmailField(required=False, help_text="Email from Google account")
    name = serializers.CharField(required=False, help_text="Full name from Google account")
    first_name = serializers.CharField(required=False, help_text="First name from Google account")
    last_name = serializers.CharField(required=False, help_text="Last name from Google account")
    picture = serializers.URLField(required=False, help_text="Profile picture URL from Google")

class GoogleConnectSerializer(serializers.Serializer):
    """Serializer for connecting existing account to Google"""
    email = serializers.EmailField(help_text="Email of existing account")
    password = serializers.CharField(help_text="Password of existing account")
    id_token = serializers.CharField(help_text="Google ID token")

class GoogleAuthResponseSerializer(serializers.Serializer):
    """Response serializer for Google auth"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_new_user = serializers.BooleanField()
    message = serializers.CharField()

def verify_google_token(id_token):
    """Verify Google ID token and extract user info"""
    try:
        # For production, you should verify the token with Google
        # For now, we'll trust the client (in production, verify with Google's API)
        import base64
        import json
        
        # Decode the JWT token (this is a simplified version)
        # In production, use Google's verification API
        parts = id_token.split('.')
        if len(parts) != 3:
            return None
            
        # Decode payload (middle part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        user_info = json.loads(decoded)
        
        return {
            'email': user_info.get('email'),
            'name': user_info.get('name', ''),
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'picture': user_info.get('picture', ''),
            'google_id': user_info.get('sub'),
        }
    except Exception as e:
        print(f"Error verifying Google token: {e}")
        return None

class GoogleSignInView(APIView):
    """
    Google Sign-In endpoint that handles both new user registration and existing user login
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Google Sign-In (Login or Register)",
        request_body=GoogleTokenSerializer,
        responses={
            200: GoogleAuthResponseSerializer,
            400: "Invalid token or missing data",
            401: "Authentication failed"
        }
    )
    def post(self, request):
        serializer = GoogleTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        id_token = serializer.validated_data.get('id_token')
        
        # Verify Google token and get user info
        google_user_info = verify_google_token(id_token)
        if not google_user_info:
            return Response(
                {"detail": "Invalid Google token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        email = google_user_info['email']
        if not email:
            return Response(
                {"detail": "No email found in Google account"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        try:
            user = User.objects.get(email=email)
            is_new_user = False
            message = "Successfully signed in with Google"
        except User.DoesNotExist:
            # Create new user
            with transaction.atomic():
                user = User.objects.create(
                    email=email,
                    first_name=google_user_info.get('first_name', ''),
                    last_name=google_user_info.get('last_name', ''),
                    is_active=True,
                )
                # Set an unusable password since they're using Google auth
                user.set_unusable_password()
                user.save()
            is_new_user = True
            message = "Account created successfully with Google"

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "access": str(access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_new_user": is_new_user,
            "message": message
        }, status=status.HTTP_200_OK)

class GoogleConnectAccountView(APIView):
    """
    Connect existing account to Google
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Connect existing account to Google",
        request_body=GoogleConnectSerializer,
        responses={
            200: GoogleAuthResponseSerializer,
            400: "Invalid credentials or token",
            401: "Authentication failed"
        }
    )
    def post(self, request):
        serializer = GoogleConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        id_token = serializer.validated_data['id_token']

        # Verify Google token
        google_user_info = verify_google_token(id_token)
        if not google_user_info:
            return Response(
                {"detail": "Invalid Google token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate existing user
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response(
                {"detail": "Invalid email or password"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if Google email matches user email
        if google_user_info['email'] != email:
            return Response(
                {"detail": "Google account email doesn't match user email"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user with Google info (optional)
        user.first_name = google_user_info.get('first_name', user.first_name)
        user.last_name = google_user_info.get('last_name', user.last_name)
        user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "access": str(access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_new_user": False,
            "message": "Account successfully connected to Google"
        }, status=status.HTTP_200_OK)

class GoogleRegisterView(APIView):
    """
    Register new account using Google email and custom password
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new account with Google email and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'password']
        ),
        responses={
            201: GoogleAuthResponseSerializer,
            400: "Email already exists or invalid data"
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email or not password:
            return Response(
                {"detail": "Email and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "Account with this email already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new user
        with transaction.atomic():
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            user.set_password(password)
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "access": str(access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_new_user": True,
            "message": "Account created successfully"
        }, status=status.HTTP_201_CREATED)

class GoogleAuthStatusView(APIView):
    """
    Check if user has Google account connected
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Check Google account connection status",
        responses={
            200: serializers.Serializer({
                'has_google_connected': serializers.BooleanField(),
                'email': serializers.EmailField(),
                'can_connect_google': serializers.BooleanField(),
            })
        }
    )
    def get(self, request):
        user = request.user
        
        # Check if user has Google social account connected
        # This would require checking social account models
        has_google_connected = False  # Implement based on your social account setup
        
        return Response({
            'has_google_connected': has_google_connected,
            'email': user.email,
            'can_connect_google': not has_google_connected,
        })
