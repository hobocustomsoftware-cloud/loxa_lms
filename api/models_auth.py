# api/models_auth.py
from django.db import models
from django.utils import timezone
import uuid

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=32, db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, default="login")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    def expired(self):
        return timezone.now() > self.expires_at
