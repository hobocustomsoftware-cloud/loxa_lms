from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest
from .models import Org

class CurrentOrgMiddleware(MiddlewareMixin):
    """
    X-Org-ID header ကနေ Org ကို attach လုပ်ပေးမယ် (request.org)
    header မပါ/မမှန် → request.org မတင်ဘူး (permission က စစ်သွားမယ်)
    """
    def process_request(self, request: HttpRequest):
        org_id = request.headers.get("X-Org-ID") or request.META.get("HTTP_X_ORG_ID")
        if not org_id:
            return  # permission layer မှာ message ပေးမယ်
        try:
            request.org = Org.objects.get(pk=org_id) # type: ignore
        except Org.DoesNotExist:
            # permission layer မှာ ပိုပြီး readable message ပေးမယ်
            request.org = None # type: ignore