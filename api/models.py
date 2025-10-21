from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class LiveSession(models.Model):
    org = models.ForeignKey("orgs.Org", on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    channel_name = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_sessions")
    start_time = models.DateTimeField(default=timezone.now)
    duration_minutes = models.PositiveIntegerField(default=60)
    max_participants = models.PositiveIntegerField(default=20)
    recording_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-start_time"]
    def __str__(self):
        return str(self.title or self.channel_name or f"Session {self.pk}")

class SeatReservation(models.Model):
    STATE_CHOICES = [("PENDING","PENDING"), ("CONFIRMED","CONFIRMED"), ("RELEASED","RELEASED")]
    org = models.ForeignKey("orgs.Org", on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name="seats")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seat_reservations")
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default="CONFIRMED")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = [("org","session","user")]
    def __str__(self):
        return f"Seat({self.pk}) user={getattr(self.user,'id',None)} sess={getattr(self.session,'id',None)}"

class Attendance(models.Model):
    org = models.ForeignKey("orgs.Org", on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name="attendance")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance")
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    total_seconds = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = [("org","session","user")]
    def __str__(self):
        return f"Att({self.pk}) user={getattr(self.user,'id',None)} sess={getattr(self.session,'id',None)}"



from .models_academics import Course, Module, Lesson, LessonAsset