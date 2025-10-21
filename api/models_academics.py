from django.db import models
from django.conf import settings
from django.utils.text import slugify
from orgs.models import Level, Org
from .utils_autofill import smart_slug, next_code_for_org
from .utils_paths import asset_upload_to
import uuid

User = settings.AUTH_USER_MODEL

class Course(models.Model):
    org   = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="courses", null=True, blank=True)
    level  = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="courses")
    title  = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    code   = models.CharField(max_length=50, blank=True)   # ❗ unique=False
    paper_no = models.CharField(max_length=20, blank=True)  # for university papers
    owner  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        unique_together = [("level","code")]  # ✅ scope
        indexes = [models.Index(fields=["level", "title"])]

    def save(self, *args, **kwargs):
        if not self.code:
            base = slugify(self.title)[:8].upper()  # eg. COMPUTER -> COMPUTE
            self.code = f"{base}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"


class Module(models.Model):
    org   = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="modules", null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title  = models.CharField(max_length=255)
    order  = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = [("course","title")]
        ordering = ["order","id"]
    def __str__(self): return f"{self.course} / {self.title}"

class Lesson(models.Model):
    org   = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="lessons", null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title  = models.CharField(max_length=255)
    order  = models.PositiveIntegerField(default=0)
    live_session = models.ForeignKey("api.LiveSession", on_delete=models.SET_NULL, null=True, blank=True)
    published = models.BooleanField(default=False)
    is_preview = models.BooleanField(default=False)
    class Meta:
        unique_together = [("module","title")]
        ordering = ["order","id"]
    def __str__(self): return f"{self.module} / {self.title}"


def asset_upload_to(instance, filename):
    # MEDIA_ROOT/org/<id>/lesson/<id>/asset/<ts>_<name>
    import time, os
    name = os.path.basename(filename)
    return f"org/{instance.org_id}/lesson/{instance.lesson_id}/asset/{int(time.time())}_{name}"

class LessonAsset(models.Model):
    TYPES = [("PDF","PDF"), ("VIDEO","VIDEO"), ("RECORDING","RECORDING")]
    org    = models.ForeignKey(Org, on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assets")
    type   = models.CharField(max_length=20, choices=TYPES)
    file   = models.FileField(upload_to=asset_upload_to, blank=True, null=True)
    storage_key = models.CharField(max_length=500, blank=True)
    ready  = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(default=0)
    size_bytes = models.BigIntegerField(default=0)
    is_preview = models.BooleanField(default=False)   # intro/free-to-view
    published  = models.BooleanField(default=True)    # hide/unhide switch
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
         indexes = [
            models.Index(fields=["org","lesson","type","ready"], name="asset_ready_idx"),
            models.Index(fields=["lesson","published","is_preview"], name="asset_vis_idx"),
        ]
    def save(self, *args, **kwargs):
        if not self.storage_key:
            fname = f"{uuid.uuid4().hex}_{self.type}.dat"
            self.storage_key = f"org/{self.org_id}/lesson/{self.lesson_id}/asset/{fname}" # type: ignore
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.type} {self.pk}"



class Enrollment(models.Model):
    org = models.ForeignKey("orgs.Org", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "user")