from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PhoneBackend(BaseBackend):
    """
    authenticate(request, phone=..., **kwargs)
    """
    def authenticate(self, request, phone=None, **kwargs):
        if not phone: return None
        try:
            return User.objects.get(phone_number=phone, is_active=True)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
