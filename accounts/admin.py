# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("id", "email", "phone_number", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "phone_number", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone_number")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    # username field ကို email နဲ့ပြောင်းသောက်ထား—admin form တွေ အလိုအလျောက်ပေါ်မယ်
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if hasattr(form.base_fields.get("username"), "label"): # type: ignore
            form.base_fields["username"].label = "Email" # type: ignore
        return form
