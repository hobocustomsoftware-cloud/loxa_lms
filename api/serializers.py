from django.http import JsonResponse
from rest_framework import serializers

from api.models import Attendance, LiveSession, SeatReservation
from orgs.models import Level
from .models_academics import Course, Module, Lesson, LessonAsset
from django.contrib.auth import get_user_model


User = get_user_model()

class LevelSer(serializers.ModelSerializer):
    program_title = serializers.CharField(source="program.title", read_only=True)

    class Meta:
        model = Level
        fields = ("id", "label", "program_title")


class UserSer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class CourseSer(serializers.ModelSerializer):
    level_label   = serializers.SerializerMethodField()
    program_label = serializers.SerializerMethodField()
    org_name      = serializers.CharField(source="org.name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "description", "code", "paper_no", "org",
            "org_name", "level", "owner", "level_label", "program_label",
        ]
        read_only_fields = ("org",)

    def get_level_label(self, obj):
        return getattr(obj.level, "label", None) if obj.level else None

    def get_program_label(self, obj):
        if obj.level and getattr(obj.level, "program", None):
            return obj.level.program.title
        return None

    def create(self, validated_data):
        return Course.objects.create(**validated_data)

        return None

class LessonSer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ("org",)

class AssetSer(serializers.ModelSerializer):
    class Meta:
        model = LessonAsset
        fields = "__all__"
        read_only_fields = ("org","ready","size_bytes","duration_seconds")



class LiveSessionSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = LiveSession
        fields = [
            "id", "org", "title", "channel_name", "owner", "owner_username",
            "start_time", "duration_minutes", "max_participants", "recording_enabled", "created_at"
        ]
        read_only_fields = ["id", "owner", "channel_name"]

class SeatReservationSer(serializers.ModelSerializer):
    class Meta:
        model = SeatReservation
        fields = "__all__"

class AttendanceSer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = "__all__"




class JoinResponseSer(serializers.Serializer):
    # session_id = serializers.IntegerField()
    # user_id = serializers.IntegerField()
    # joined_at = serializers.DateTimeField()
    # message = serializers.CharField(default="Joined successfully")
    channel = serializers.CharField()
    uid = serializers.CharField()
    rtc_token = serializers.CharField()
    expires_at = serializers.DateTimeField()

class LeaveResponseSer(serializers.Serializer):
    # session_id = serializers.IntegerField()
    # user_id = serializers.IntegerField()
    # left_at = serializers.DateTimeField()
    # duration_seconds = serializers.IntegerField()
    # message = serializers.CharField(default="Left successfully")
    ok = serializers.BooleanField()




class OrgBoundSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True

    def create(self, validated_data):
        req = self.context.get("request")
        if req and getattr(req, "org", None):
            validated_data["org"] = req.org
        validated_data.pop("org", None)  # client org ignore
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("org", None)
        return super().update(instance, validated_data)






class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonAsset
        fields = ("id", "type")

class LessonNestedSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    class Meta:
        model = Lesson
        fields = ("id", "title", "assets")

class ModuleNestedSerializer(serializers.ModelSerializer):
    lessons = LessonNestedSerializer(many=True, read_only=True)
    class Meta:
        model = Module
        fields = ("id", "title", "lessons")

class CourseTreeSerializer(serializers.ModelSerializer):
    modules = ModuleNestedSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        fields = ("id", "title", "modules")