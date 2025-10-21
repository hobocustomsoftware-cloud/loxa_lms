# api/routers.py
from collections import OrderedDict
from django.urls import reverse, NoReverseMatch
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny


class HybridRouter(DefaultRouter):
    def __init__(self, extra_root_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_root_names = extra_root_names or {}

    def get_api_root_view(self, api_urls=None):
        # original DRF root view (already wired with api_root_dict, etc.)
        original_view = super().get_api_root_view(api_urls)
        extra = self.extra_root_names

        def api_root(request, *args, **kwargs):
            # call the original view first
            resp = original_view(request, *args, **kwargs)
            # inject extra links (if any)
            try:
                data = OrderedDict(resp.data) # type: ignore
                for label, url_name in extra.items():
                    try:
                        data[label] = reverse(url_name, request=request) # type: ignore
                    except NoReverseMatch:
                        pass
                resp.data = data # type: ignore
            except Exception:
                # if anything odd, just return original response
                return resp
            return resp

        # keep DRF’s metadata so schema/browsable UI keep working
        api_root.cls = getattr(original_view, "cls", None) # type: ignore
        api_root.initkwargs = getattr(original_view, "initkwargs", {}) # type: ignore

        # make the root page public (but DON’T touch your viewsets’ permissions)
        if api_root.cls: # type: ignore
            api_root.cls.permission_classes = [AllowAny] # type: ignore
            api_root.cls.authentication_classes = [] # type: ignore

        return api_root
