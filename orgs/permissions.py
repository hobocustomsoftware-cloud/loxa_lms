# orgs/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrgMemberOrPreviewReadOnly(BasePermission):
    """
    - SAFE methods (GET/HEAD/OPTIONS):
        * login + org member => OK
        * anonymous => OK (later view will restrict to preview-only)
    - Non-SAFE methods:
        * org member + authenticated only
    Supports both accounts.OrganizationMembership and orgs.OrgMembership layouts.
    """
    message = "Not allowed."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        org = getattr(request, "org", None)
        if not (user and user.is_authenticated and org):
            return False

        # accounts.OrganizationMembership (custom auth model)
        try:
            if user.org_memberships.filter(org=org).exists():
                return True
        except Exception:
            pass

        # orgs.OrgMembership (alternate org model)
        try:
            from .models import OrgMembership
            return OrgMembership.objects.filter(org=org, user=user).exists()
        except Exception:
            return False
