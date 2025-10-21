# middleware.py
import os, re
from django.http import JsonResponse
from orgs.models import Org
from django.utils.deprecation import MiddlewareMixin
from typing import Optional


PUBLIC_PATH = re.compile(r"^/api/(courses|modules|lessons,assets)/")

class OrgMiddleware:
    def __call__(self, request):
        request.org = None
        org_id = request.headers.get("X-Org-ID")
        if org_id:
            try:
                request.org = Org.objects.get(pk=org_id) # type: ignore
            except Org.DoesNotExist: # type: ignore
                # Header မှားပို့ရင် public-only ပြတယ် (403 မပစ်တော့)
                request.org = None
        return self.get_response(request) # type: ignore





try:
    # your Org model path; change if different
    from orgs.models import Org
except Exception:  # during early migrate, model might not be ready
    Org = None  # type: ignore




class TenantResolver(MiddlewareMixin):
    """
    Read X-Org-ID from request headers and attach request.org.
    If header is missing, leave request.org = None (public endpoints can allow it).
    If invalid org id is provided, return 403.
    """

    def process_request(self, request):
        org_id = request.headers.get("X-Org-ID")
        request.org: Optional[object] = None # type: ignore

        # no header → allow None (your view/permission will decide)
        if not org_id:
            return None

        # model may not be ready before migrations
        if Org is None:
            return JsonResponse({"detail": "Org model not ready"}, status=503)

        # validate
        try:
            request.org = Org.objects.get(id=org_id)
        except Org.DoesNotExist:
            return JsonResponse({"detail": "Invalid X-Org-ID"}, status=403)

        return None


# (optional) very lightweight CORS for local dev if you haven't set django-cors-headers
# class SimpleCORS(MiddlewareMixin):
#     def process_response(self, request, response):
#         # adjust as you need for dev
#         response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
#         response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Org-ID"
#         response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
#         return response