# api/views_crud.py
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Prefetch
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from api.models import Attendance, LiveSession
from orgs.permissions import IsOrgMemberOrPreviewReadOnly
from .models_academics import Course, Enrollment, Module, Lesson, LessonAsset
from .serializers import CourseSer, CourseTreeSerializer,  LessonSer, AssetSer
from .serializers_academics import LessonAssetSerializer, ModuleSer  # ဘယ် serializer သံုးထားသလဲအပေါ်မူတည်





ORG_HEADER = openapi.Parameter(
    "X-Org-ID", openapi.IN_HEADER, description="Current Org ID",
    type=openapi.TYPE_STRING, required=True
)

def _has_org(Model):
    return Model and any(getattr(f, "name", None) == "org" for f in Model._meta.get_fields())

class BaseOrgViewSet(ModelViewSet):
    permission_classes = [IsOrgMemberOrPreviewReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            Model = getattr(getattr(self, "serializer_class", None), "Meta", None)
            Model = getattr(Model, "model", None)
            return Model.objects.none() if Model else []
        # ❗ org filtering မလုပ် — child viewset မှာပဲ စီမံမယ်
        Model = getattr(getattr(self, "serializer_class", None), "Meta", None)
        Model = getattr(Model, "model", None)
        return Model.objects.all() if Model else []




class CourseViewSet(BaseOrgViewSet, viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = CourseSer  # list/detail meta
    queryset = Course.objects.select_related("level", "level__program")

    def get_queryset(self):
        qs  = super().get_queryset()
        org = getattr(self.request, "org", None)

        if org:
            # org header ပါရင် org matched + public နှစ်မျိုးလုံးပြ
            qs = qs.filter(Q(org=org) | Q(org__isnull=True))  # type: ignore
        else:
            # header မပို့ရင် public only
            qs = qs.filter(org__isnull=True)  # type: ignore

        return qs.select_related("org", "level", "level__program").prefetch_related(
            Prefetch(
                "modules",
                queryset=Module.objects.order_by("order", "id").prefetch_related(
                    Prefetch(
                        "lessons",
                        queryset=Lesson.objects.order_by("order", "id").prefetch_related(
                            Prefetch(
                                "assets",
                                queryset=LessonAsset.objects.order_by("id"),
                            )
                        ),
                    )
                ),
            )
        )

    def get_serializer_class(self):
        # အခု meta/detail လည်း CourseSer တစ်ခုပဲသုံးထားတယ်
        return CourseSer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = self.request.user
        enrolled_ids: set[int] = set()
        if user.is_authenticated:
            enrolled_ids = set(
                Enrollment.objects.filter(user=user).values_list("course_id", flat=True)
            )
        ctx["enrolled_course_ids"] = enrolled_ids
        return ctx

    def get_permissions(self):
        if self.action in ("list", "retrieve", "tree"):
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=["get"],
        url_path="tree",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def tree(self, request, pk=None):
        course = self.get_object()
        mods = Module.objects.filter(course=course).order_by("order", "id")
        lessons = Lesson.objects.filter(module__course=course).order_by("order", "id")

        assets_qs = LessonAsset.objects.filter(lesson__module__course=course)

        # anonymous user အတွက် preview only ထုတ်ချင်ရင် uncomment
        # if not request.user.is_authenticated:
        #     assets_qs = assets_qs.filter(is_preview=True, published=True)

        assets_by_lesson: dict[int, list[dict]] = {}
        for a in assets_qs:
            rel = a.file.url if a.file else ""
            absu = request.build_absolute_uri(rel) if rel else ""
            assets_by_lesson.setdefault(a.lesson_id, []).append({
                "id": a.id,
                "type": a.type,              # "VIDEO" | "RECORDING" | "PDF"
                "is_preview": getattr(a, "is_preview", False),
                "file": rel,                 # e.g. /media/lesson1.mp4
                "abs_url": absu,             # e.g. http://localhost:8000/media/lesson1.mp4
                "ready": a.ready,
                "size_bytes": a.size_bytes,
                "duration_seconds": a.duration_seconds,
            })

        data = []
        for m in mods:
            ms = []
            for l in lessons.filter(module=m):
                ms.append({
                    "id": l.id,
                    "title": l.title,
                    "assets": assets_by_lesson.get(l.id, []),
                })
            data.append({"id": m.id, "title": m.title, "lessons": ms})

        return Response({
            "id": course.id,
            "title": course.title,
            "modules": data
        })
    




class ModuleFilter(FilterSet):
    course = NumberFilter(field_name="course_id", lookup_expr="exact")
    class Meta:
        model = Module
        fields = ["course"]


class ModuleViewSet(BaseOrgViewSet, viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = ModuleSer
    queryset = Module.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ModuleFilter

    def perform_create(self, serializer):
        # Module မှာ file/size_bytes မရှိဆို org ထည့်ပေးရုံ
        serializer.save(org=getattr(self.request, "org", None))


class LessonFilter(FilterSet):
    course = NumberFilter(field_name="module__course_id", lookup_expr="exact")
    module = NumberFilter(field_name="module_id", lookup_expr="exact")
    class Meta:
        model = Lesson
        fields = ["course", "module", "is_preview", "published"]


class LessonViewSet(BaseOrgViewSet, viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LessonSer
    queryset = Lesson.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = LessonFilter

    def perform_create(self, serializer):
        serializer.save(org=getattr(self.request, "org", None))


class AssetFilter(FilterSet):
    lesson = NumberFilter(field_name="lesson_id", lookup_expr="exact")
    course = NumberFilter(field_name="lesson__module__course_id", lookup_expr="exact")
    class Meta:
        model = LessonAsset
        fields = ["lesson", "course"]


class LessonAssetViewSet(BaseOrgViewSet, viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = AssetSer  # သင့် Serializer နဲ့ကိုက်ညီအောင်
    queryset = LessonAsset.objects.filter(published=True, ready=True)
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AssetFilter

    def get_queryset(self):
        qs = super().get_queryset()
        # Anonymous → preview & published only (safe methods)
        if self.request.method in SAFE_METHODS and not self.request.user.is_authenticated:
            qs = qs.filter(is_preview=True, published=True) # type: ignore
        return qs

    def perform_create(self, serializer):
        f = self.request.FILES.get("file")
        size = getattr(f, "size", 0) or 0
        serializer.save(org=getattr(self.request, "org", None), size_bytes=size)


    @action(detail=True, methods=["GET"])
    def open(self, request, pk=None):
        asset = self.get_object()
        course_id = asset.lesson.module.course_id
        can_view = asset.is_preview
        if request.user.is_authenticated:
            can_view = can_view or Enrollment.objects.filter(
                user=request.user, course_id=course_id
            ).exists()
        if not can_view:
            return Response({"detail":"Locked"}, status=status.HTTP_403_FORBIDDEN)

        # TODO: generate and return time-limited URL (S3, GCS, etc.)
        return Response({"url": asset.file.url})





class CourseTreeView(generics.RetrieveAPIView):
    serializer_class = CourseTreeSerializer
    queryset = Course.objects.all()

    def get_queryset(self):
        asset_qs  = LessonAsset.objects.all().only("id","type","lesson_id")
        lesson_qs = Lesson.objects.all().only("id","title","module_id").prefetch_related(
            Prefetch("assets", queryset=asset_qs)
        )
        module_qs = Module.objects.all().only("id","title","course_id").prefetch_related(
            Prefetch("lessons", queryset=lesson_qs)
        )
        return Course.objects.only("id","title").prefetch_related(
            Prefetch("modules", queryset=module_qs)
        )




class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
        })



class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"detail":"forbidden"}, status=403)
        return Response({
            "courses": Course.objects.count(),
            "modules": Module.objects.count(),
            "lessons": Lesson.objects.count(),
            "sessions": LiveSession.objects.count(),
            "attendance": Attendance.objects.count(),
        })