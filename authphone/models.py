# authphone/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
import hashlib

def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=20, db_index=True)
    code_hash = models.CharField(max_length=64)  # sha256
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    last_sent_at = models.DateTimeField(default=timezone.now)
    # optional link (created-after verify)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for(cls, phone: str, code: str, ttl_sec: int = 300):
        return cls.objects.create(
            phone=phone,
            code_hash=_hash(code),
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_sec),
            attempts=0, max_attempts=5, last_sent_at=timezone.now()
        )

    def verify(self, code: str) -> bool:
        if timezone.now() > self.expires_at:
            return False
        if self.attempts >= self.max_attempts:
            return False
        ok = self.code_hash == _hash(code)
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return ok and (timezone.now() <= self.expires_at)
