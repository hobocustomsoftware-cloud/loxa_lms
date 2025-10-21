# orgs/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOrgMemberOrPreviewReadOnly(BasePermission):
    """
    - SAFE methods (GET/HEAD/OPTIONS):
        * login + org member => OK
        * anonymous => OK (later view will restrict to preview-only)
    - Non-SAFE methods:
        * org member + authenticated only
    """
    message = "Not allowed."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        org = getattr(request, "org", None)
        return bool(user and user.is_authenticated and org and
                    user.orgmembership.filter(org=org).exists())
