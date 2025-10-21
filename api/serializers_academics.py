from rest_framework import serializers
from .models_academics import Course, Enrollment, Module, Lesson, LessonAsset

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



class ModuleSer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id","org","course","title","order"]
        read_only_fields=["org"]


class LessonAssetSerializer(serializers.ModelSerializer):
    locked = serializers.SerializerMethodField()

    class Meta:
        model = LessonAsset
        fields = ("id","type","file","storage_key","ready","duration_seconds",
                "size_bytes","is_preview","published","locked")

    def get_locked(self, obj: LessonAsset):
        # serializer context ထဲက enrolled_course_ids (set[int]) သုံးမယ်
        enrolled_ids = self.context.get("enrolled_course_ids", set())
        # asset ရဲ့ course id
        course_id = getattr(obj.lesson.module.course, "id", None)
        if not obj.published:
            return True
        if obj.is_preview:
            return False
        if course_id and course_id in enrolled_ids:
            return False
        return True


class LessonSer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()
    assets = LessonAssetSerializer(many=True, read_only=True)
    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields=["org"]

    def get_is_locked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return not obj.is_preview
        # enrolled?
        enrolled = Enrollment.objects.filter(course=obj.module.course, user=request.user).exists()
        return (not enrolled) and (not obj.is_preview)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Lock ဖြစ်ရင် body မပို့ချင်ရင်:
        if data.get("is_locked"):
            data["body"] = ""  # or omit: data.pop("body", None)
        return data

