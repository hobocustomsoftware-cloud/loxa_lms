# authphone/admin.py
from django.contrib import admin
from .models import PhoneOTP

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone","expires_at","attempts","max_attempts","created_at")
    search_fields = ("phone",)
    readonly_fields = ("code_hash",)
