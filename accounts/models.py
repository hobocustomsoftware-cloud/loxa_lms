# accounts/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager, Group
)
from django.conf import settings

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter # type: ignore

# ==== NEW: Role model (global roles only) =====================
class Role(models.Model):
    """
    Global roles for a user (not org-scoped).
    Slugs we use: super_admin, admin, editor, moderator
    """
    slug = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.name or self.slug

GLOBAL_ROLE_SLUGS = ("super_admin", "admin", "editor", "moderator", "teacher", "student", "parent")
# =============================================================

class UserManager(BaseUserManager):
    use_in_migrations = True
    def normalize_email(self, email):
        return super().normalize_email(email) if email else email
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        if not password:
            raise ValueError("Superuser must have a password")
        return self.create_user(email, password, **extra)
    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name  = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # ==== NEW: Many-to-many user→Role (global roles) ==========
    roles = models.ManyToManyField(Role, blank=True, related_name="users")
    # ==========================================================

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self):
        return self.email or f"User#{self.pk}"

    # ---- Convenience flags (global) ----
    @property
    def is_admin(self) -> bool:
        # admin if: is_staff / is_superuser / has Role(admin/super_admin) / in Group(admin/super_admin)
        if self.is_superuser:
            return True
    # Role/Group အပေါ်သာ အခြေခံ
        return (
            self.roles.filter(slug__in=["admin", "super_admin"]).exists()
            or self.groups.filter(name__in=["admin", "super_admin"]).exists()
        )

    @property
    def is_editor(self) -> bool:
        return (
            self.roles.filter(slug__in=["editor", "admin", "super_admin"]).exists()
            or self.groups.filter(name__in=["editor", "admin", "super_admin"]).exists()
        )

    @property
    def is_moderator(self) -> bool:
        return (
            self.roles.filter(slug__in=["moderator", "admin", "super_admin"]).exists()
            or self.groups.filter(name__in=["moderator", "admin", "super_admin"]).exists()
        )

    def has_global_role(self, role_slug: str) -> bool:
        return (
            self.roles.filter(slug=role_slug).exists()
            or self.groups.filter(name=role_slug).exists()
        )

    # Nice helpers
    def add_role(self, role_slug: str):
        role, _ = Role.objects.get_or_create(
            slug=role_slug, defaults={"name": role_slug.replace("_", " ").title()}
        )
        self.roles.add(role)
        # keep Django Group in sync (optional but useful for admin/permissions)
        grp, _ = Group.objects.get_or_create(name=role_slug)
        self.groups.add(grp)

    def remove_role(self, role_slug: str):
        self.roles.filter(slug=role_slug).delete()
        try:
            grp = Group.objects.get(name=role_slug)
            self.groups.remove(grp)
        except Group.DoesNotExist:
            pass

# ---------- Organization-scoped roles ----------
class OrgRole(models.TextChoices):
    OWNER   = "owner",   "Owner"
    ADMIN   = "admin",   "Organization Admin"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"

class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

ORGANIZATION_MODEL = getattr(settings, "AUTH_ORG_MODEL", "accounts.Organization")

class OrganizationMembership(models.Model):
    org  = models.ForeignKey(ORGANIZATION_MODEL, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships")
    role = models.CharField(max_length=20, choices=OrgRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("org", "user")]
        indexes = [
            models.Index(fields=["org", "user"]),
            models.Index(fields=["user", "role"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.org} ({self.role})"

# ---- User helper methods (org-scope) ----
def _user_has_org_role(user: User, org, role: str) -> bool:
    return OrganizationMembership.objects.filter(org=org, user=user, role=role).exists()

def _user_org_role(user: User, org) -> str | None:
    m = OrganizationMembership.objects.filter(org=org, user=user).only("role").first()
    return m.role if m else None

# Avoid double registration on autoreload
if not hasattr(User, "has_org_role"):
    User.add_to_class("has_org_role", _user_has_org_role)
if not hasattr(User, "org_role"):
    User.add_to_class("org_role", _user_org_role)




