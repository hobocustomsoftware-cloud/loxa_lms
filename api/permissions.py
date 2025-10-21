# api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models_academics import Enrollment, Lesson

class IsSessionModeratorOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(obj, "owner_id", None) == request.user.id:
            return True
        # TODO: implement is_moderator check (OrgRole, Program staff, Course teacher etc.)
        return getattr(request.user, "is_staff", False)



class IsEnrolledOrPreview(BasePermission):
    message = "Enroll လုပ်ပြီးမှ ဒီအကြောင်းအရာကို ကြည့်နိုင်ပါတယ်။"

    def has_object_permission(self, request, view, obj: Lesson):
        if obj.is_preview:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(course=obj.module.course, user=request.user).exists()



