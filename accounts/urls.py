from django.urls import path
from .views import PhoneRegisterView, PhoneLoginView

urlpatterns = [
    path("phone/register/", PhoneRegisterView.as_view(), name="phone-register"),
    path("phone/login/", PhoneLoginView.as_view(), name="phone-login"),
]
