import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models_academics import Lesson, LessonAsset
from orgs.permissions import IsOrgMember
from .utils_sign import SIGNER, sign_path

def _build_media_path(*parts):
    safe = [str(p).replace("..","").lstrip("/") for p in parts]
    return os.path.join(settings.MEDIA_ROOT, *safe)

class AssetInit(APIView):
    """Create a placeholder LessonAsset, return upload path (relative)."""
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    def post(self, request, lesson_id):
        org = request.org
        lesson = get_object_or_404(Lesson, pk=lesson_id, org=org)
        a_type = request.data.get("type","PDF")
        asset = LessonAsset.objects.create(
            org=org, lesson=lesson, type=a_type, storage_key="", ready=False
        )
        rel_base = f"org/{org.id}/course/{lesson.module.course.id}/lesson/{lesson.id}/asset/{asset.id}" # type: ignore
        # client will PUT file to /api/assets/<id>/upload/?name=source
        asset.storage_key = f"{rel_base}/source"
        asset.save(update_fields=["storage_key"])
        return Response({"asset_id": asset.id, "upload_field": "source", "rel_base": rel_base}) # type: ignore

class AssetUpload(APIView):
    """Simple multipart upload into MEDIA_ROOT (no S3)."""
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    def post(self, request, pk):
        org = request.org
        asset = get_object_or_404(LessonAsset, pk=pk, org=org)
        f = request.FILES.get("file")
        if not f:
            return Response({"detail":"file required"}, status=400)
        abs_path = _build_media_path(asset.storage_key)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)
        asset.size_bytes = f.size
        asset.ready = True  # if you want HLS pipeline later, set False here and flip after processing
        asset.save(update_fields=["size_bytes","ready"])
        return Response({"ok": True, "asset_id": asset.id}) # type: ignore

class AssetPlay(APIView):
    """Return signed URL; prefer HLS if exists."""
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    def get(self, request, pk):
        org = request.org
        asset = get_object_or_404(LessonAsset, pk=pk, org=org, ready=True)
        rel_path = asset.storage_key  # e.g. .../asset/77/source
        base_dir = rel_path.rsplit("/",1)[0]
        abs_dir = _build_media_path(base_dir)
        if asset.type in ("VIDEO","RECORDING"):
            hls = os.path.join(abs_dir, "hls", "index.m3u8")
            if os.path.exists(hls):
                rel_path = f"{base_dir}/hls/index.m3u8"
        token = sign_path(rel_path)
        return Response({"url": f"/protected/media?token={token}"})

class ProtectedMedia(APIView):
    """Nginx X-Accel-Redirect; validates token & points to alias."""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        token = request.GET.get("token")
        if not token: return HttpResponseForbidden("missing token")
        try:
            rel = SIGNER.unsign(token, max_age=3600)  # 1 hour
        except Exception:
            return HttpResponseForbidden("invalid token")
        # internal redirect path must match nginx.conf `/_internal_media/`
        resp = HttpResponse()
        resp["X-Accel-Redirect"] = f"/_internal_media/{rel}"
        # allow range for video
        resp["Accept-Ranges"] = "bytes"
        return resp
