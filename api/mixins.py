from rest_framework.exceptions import PermissionDenied

class OrgScopedMixin:
    def get_queryset(self):
        qs = super().get_queryset() # type: ignore
        org = getattr(self.request, "org", None) # type: ignore
        if not org:
            raise PermissionDenied("Missing org (set X-Org-ID header)")
        return qs.filter(org=org)

    def perform_create(self, serializer):
        org = getattr(self.request, "org", None) # type: ignore
        if not org:
            raise PermissionDenied("Missing org")
        serializer.save(org=org)