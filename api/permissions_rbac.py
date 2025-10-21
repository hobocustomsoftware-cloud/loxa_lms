from rest_framework.permissions import BasePermission, IsAuthenticated

def _roles_from(request):
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated:
        return set(), {}
    # JWTAuth backend လိုက်ဖတ်ပြီး request.auth.payload ထဲက claims ယူနိုင်စေ
    payload = getattr(request, "auth", None)
    payload = getattr(payload, "payload", payload) or {}
    roles = set(payload.get("roles", []))
    org_roles = payload.get("org_roles", {})  # {"1": ["org_admin", ...]}
    return roles, org_roles

class RoleRequired(BasePermission):
    """Global role(s) required."""
    def __init__(self, *roles):
        self.required = set(roles)
    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            return False
        roles, _ = _roles_from(request)
        return bool(self.required & roles)

class AnyOf(BasePermission):
    """Combine multiple permission classes with OR."""
    def __init__(self, *perms):
        self.perms = perms
    def has_permission(self, request, view):
        return any(p().has_permission(request, view) for p in self.perms)

class OrgRoleRequired(BasePermission):
    """Org-scoped role(s) required (uses request.org)."""
    def __init__(self, *roles):
        self.required = set(roles)
    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            return False
        _, org_roles = _roles_from(request)
        org = getattr(request, "org", None)
        if not org:
            return False
        have = set(org_roles.get(str(org.id), []))
        return bool(self.required & have)
