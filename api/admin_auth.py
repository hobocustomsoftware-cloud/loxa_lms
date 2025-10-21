# api/admin_auth.py
from django.contrib import admin
from .models_auth import PhoneOTP

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "purpose", "created_at", "expires_at", "attempts", "session_id")
    search_fields = ("phone", "session_id")
    ordering = ("-created_at",)
