from django.contrib import admin, messages
from django import forms
from django.db import IntegrityError, transaction
from django.db import transaction
from django.utils import timezone

from .models import LiveSession, SeatReservation, Attendance
from .models_academics import Lesson

from .models_academics import  Level, Course, Module, Lesson, LessonAsset



class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("level","title","paper_no","owner")  # ✅ org/description မပါ
    def save(self, commit=True):
        try:
            with transaction.atomic():
                return super().save(commit=commit)
        except IntegrityError:
            raise forms.ValidationError("Duplicate Course in this Level (level+code).")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = ("id","level","code","title","paper_no","owner", "org")
    list_filter  = ("level__program","level")
    search_fields = ("code","title","paper_no")
    readonly_fields = ("code",)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("id","course","title","order", "org")
    list_filter  = ("course",)
    search_fields = ("title",)
    ordering     = ("course","order","id")

# @admin.register(Lesson)
# class LessonAdmin(admin.ModelAdmin):
#     list_display = ("id","module","title","order","published","live_session", "is_preview")
#     list_filter  = ("module__course","module","published")
#     search_fields = ("title",)
#     ordering     = ("module","order","id")

@admin.register(LessonAsset)
class LessonAssetAdmin(admin.ModelAdmin):
    list_display = ("id","org","lesson","type","ready","created_at")
    list_filter  = ("org","type","ready")
    search_fields = ("lesson__title",)
    readonly_fields = ("storage_key","size_bytes","created_at")



class SeatReservationInline(admin.TabularInline):
    model = SeatReservation
    extra = 0
    autocomplete_fields = ["user"]
    fields = ("org", "user", "state", "expires_at", "created_at")
    readonly_fields = ("created_at",)

class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    autocomplete_fields = ["user"]
    fields = ("org", "user", "joined_at", "left_at", "total_seconds")
    readonly_fields = ()


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "org", "title", "channel_name", "owner",
        "start_time", "duration_minutes", "max_participants",
        "recording_enabled", "seats_count", "attendance_count", "created_at"
    )
    list_filter  = ("org", "recording_enabled", "owner")
    date_hierarchy = "start_time"
    search_fields = ("title", "channel_name", "owner__username", "owner__email")
    autocomplete_fields = ["org", "owner"]
    inlines = [SeatReservationInline, AttendanceInline]
    ordering = ("-start_time",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("org", "owner")

    def seats_count(self, obj): return obj.seats.count()
    seats_count.short_description = "Seats" # type: ignore

    def attendance_count(self, obj): return obj.attendance.count()
    attendance_count.short_description = "Attendance" # type: ignore

    # Handy actions
    actions = ["end_session_now"]

    @admin.action(description="End session now (set left_at for open attendances)")
    def end_session_now(self, request, queryset):
        now = timezone.now()
        updated = 0
        with transaction.atomic():
            for sess in queryset:
                rows = Attendance.objects.filter(session=sess, left_at__isnull=True).update(left_at=now)
                updated += rows
        self.message_user(request, f"Closed {updated} open attendance rows.", level=messages.SUCCESS)

# -------- SeatReservation Admin --------
@admin.register(SeatReservation)
class SeatReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "session", "user", "state", "expires_at", "created_at")
    list_filter  = ("org", "session", "state")
    search_fields = ("session__title", "session__channel_name", "user__username", "user__email")
    autocomplete_fields = ["org", "session", "user"]
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    actions = ["mark_confirmed", "mark_released"]

    @admin.action(description="Mark selected → CONFIRMED")
    def mark_confirmed(self, request, queryset):
        n = queryset.update(state="CONFIRMED", expires_at=None)
        self.message_user(request, f"{n} reservation(s) marked CONFIRMED.", level=messages.SUCCESS)

    @admin.action(description="Mark selected → RELEASEED")
    def mark_released(self, request, queryset):
        n = queryset.update(state="RELEASEED")
        self.message_user(request, f"{n} reservation(s) marked RELEASEED.", level=messages.SUCCESS)

# -------- Attendance Admin --------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "session", "user", "joined_at", "left_at", "total_seconds")
    list_filter  = ("org", "session")
    search_fields = ("session__title", "session__channel_name", "user__username", "user__email")
    # autocomplete_fields = ["org", "session", "user"]
    raw_id_fields = ["user", "session"]
    date_hierarchy = "joined_at"
    ordering = ("-joined_at",)

    actions = ["close_open_and_compute", "compute_total_seconds"]

    @admin.action(description="Close open attendance (left_at=now) + recompute total_seconds")
    def close_open_and_compute(self, request, queryset):
        now = timezone.now()
        changed = 0
        with transaction.atomic():
            for att in queryset.select_related("session", "user"):
                if att.left_at is None:
                    att.left_at = now
                if att.joined_at and att.left_at:
                    att.total_seconds = int((att.left_at - att.joined_at).total_seconds())
                att.save(update_fields=["left_at", "total_seconds"])
                changed += 1
        self.message_user(request, f"Updated {changed} attendance rows.", level=messages.SUCCESS)

    @admin.action(description="Recompute total_seconds")
    def compute_total_seconds(self, request, queryset):
        changed = 0
        with transaction.atomic():
            for att in queryset.only("id", "joined_at", "left_at"):
                if att.joined_at and att.left_at:
                    att.total_seconds = int((att.left_at - att.joined_at).total_seconds())
                    att.save(update_fields=["total_seconds"])
                    changed += 1
        self.message_user(request, f"Recomputed {changed} rows.", level=messages.SUCCESS)

# -------- Lesson Admin: expose live_session on form --------
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "module", "title", "order", "published", "live_session", "is_preview", "org")
    list_filter  = ("module__course", "module", "published")
    search_fields = ("title", "module__title", "module__course__title")
    ordering = ("module", "order", "id")
    autocomplete_fields = ["module", "live_session"]  # ✅ pick live session for this lesson
    fields = ("module", "title", "order", "published", "live_session", "is_preview", "org")



class OrgScopedAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = getattr(request, "org", None)
        return qs.filter(org=org) if org else qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.org:
            obj.org = getattr(request, "org", None)
        super().save_model(request, obj, form, change)
