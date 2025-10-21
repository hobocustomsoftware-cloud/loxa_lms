from django.urls import path
from .views import RequestOTPView, VerifyOTPView

urlpatterns = [
    path("request/", RequestOTPView.as_view(), name="phone-request"),
    path("verify/",  VerifyOTPView.as_view(),  name="phone-verify"),
]
