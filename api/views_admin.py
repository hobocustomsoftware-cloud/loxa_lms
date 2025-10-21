from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Q

from .models_academics import Course, Enrollment
from .models import LiveSession  # sessions model

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])   # dev အတွက် AllowAny လုပ်ချင်ရင် ပြောင်းနိုင်
def admin_metrics(request):
    org = getattr(request, "org", None)

    q = Q()
    if org:
        q &= (Q(org=org) | Q(org__isnull=True))

    data = {
        "courses": Course.objects.filter(q).count(),
        "sessions": LiveSession.objects.filter(q).count(),
        "enrollments": Enrollment.objects.filter(q).count(),
        "recent_courses": list(
            Course.objects.filter(q)
            .select_related("level","level__program")
            .order_by("-id")[:5]
            .values("id","title","code","level__label","level__program__title")
        ),
    }
    return Response(data)
