from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.reverse import reverse
from collections import OrderedDict
from django.urls import NoReverseMatch

# Import your views
from accounts.views import MeView
from .views_admin import admin_metrics
from . import views_crud, views_sessions, views_agora

# A custom router to add non-model endpoints to the API root view for discoverability
class MyRouter(DefaultRouter):
    class APIRootView(DefaultRouter.APIRootView):
        def get(self, request, *args, **kwargs):
            resp = super().get(request, *args, **kwargs)
            data = OrderedDict(resp.data) # type: ignore

            def safe_add(key, name):
                try:
                    data[key] = reverse(name, request=request)
                except NoReverseMatch:
                    pass

            # --- Add Custom & Third-party Endpoints for Discoverability ---

            # App-specific endpoints
            safe_add('agora-token', 'agora-token')
            safe_add('courses-tree', 'course-tree')
            safe_add('admin-metrics', 'admin-metrics')
            safe_add('auth-me', 'auth-me')

            # dj-rest-auth endpoints
            safe_add('auth-login', 'rest_login')
            safe_add('auth-logout', 'rest_logout')
            safe_add('auth-user-details', 'rest_user_details')
            safe_add('auth-password-reset', 'rest_password_reset')
            safe_add('auth-password-change', 'rest_password_change')
            safe_add('auth-token-verify', 'token_verify')
            safe_add('auth-token-refresh', 'token_refresh')

            # --- Explicitly listing Phone and Google Auth endpoints ---
            data['phone-auth (API)'] = "POST to /api/auth/phone/request/ and /api/auth/phone/verify/"
            data['google-auth (API)'] = "POST to /api/auth/google/ with 'access_token' (for mobile/SPA)"
            data['google-auth (Web)'] = request.build_absolute_uri('/api/web-auth/google/login/')


            return Response(data)

# Use the custom router
router = MyRouter()
router.register(r'live-sessions', views_sessions.LiveSessionViewSet, basename='live-session')
router.register(r"seats", views_sessions.SeatReservationViewSet, basename="seat")
router.register(r"attendance", views_sessions.AttendanceViewSet, basename="attendance")
router.register(r"courses", views_crud.CourseViewSet, basename="course")
router.register(r"modules", views_crud.ModuleViewSet, basename="module")
router.register(r"lessons", views_crud.LessonViewSet, basename="lesson")
router.register(r"assets", views_crud.LessonAssetViewSet, basename="asset")
router.register(r'agora', views_agora.AgoraViewSet, basename='agora')


# --- URL Patterns for the 'api' app ---
# These are included under the /api/ prefix in the main urls.py
urlpatterns = [
    # Router URLs for ModelViewSets
    path("", include(router.urls)),

    # Non-router endpoints (APIView / function views)
    path("agora/token/", views_agora.AgoraTokenView.as_view(), name="agora-token"),
    path("courses/<int:pk>/tree/", views_crud.CourseTreeView.as_view(), name="course-tree"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("admin/stats/", views_crud.AdminStatsView.as_view()),
    path("admin/metrics/", admin_metrics, name="admin-metrics"),

    # --- ADD THIS FOR WEB-BASED (REDIRECT) SOCIAL LOGIN ---
    # This provides URLs like /api/web-auth/google/login/ for the browser flow
    path("web-auth/", include('allauth.urls')),
]

