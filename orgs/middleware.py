from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest
from .models import Org

class CurrentOrgMiddleware(MiddlewareMixin):
    """
    X-Org-ID header ကနေ Org ကို attach လုပ်ပေးမယ် (request.org)
    header မပါ/မမှန် → request.org မတင်ဘူး (permission က စစ်သွားမယ်)
    Accepts numeric org id or slug.
    """
    def process_request(self, request: HttpRequest):
        org_id = request.headers.get("X-Org-ID") or request.META.get("HTTP_X_ORG_ID")
        if not org_id:
            return  # permission layer မှာ message ပေးမယ်
        try:
            if str(org_id).isdigit():
                request.org = Org.objects.get(pk=int(org_id))  # type: ignore
            else:
                request.org = Org.objects.get(slug=str(org_id))  # type: ignore
        except (Org.DoesNotExist, ValueError, TypeError):
            request.org = None  # type: ignore