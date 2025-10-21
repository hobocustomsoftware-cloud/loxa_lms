from allauth.socialaccount.adapter import DefaultSocialAccountAdapter # type: ignore
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter # type: ignore
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Google Login/Register လုပ်စဉ် User ကို 'student' role နှင့် group အဖြစ် သတ်မှတ်ပေးသည်။
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before any user models are saved).
        """
        user = sociallogin.user
        # If the user object already has a primary key, it's an existing user.
        # Let allauth handle the login process.
        if user.id:
            return

        # If the user is new (no ID), check if an account with that email already exists.
        # If so, allauth will automatically link them. We don't need to do anything here.
        # This simplifies the logic and avoids potential race conditions.

    def save_user(self, request, sociallogin, form=None):
        """
        User ကို database ထဲမှာ သိမ်းပြီးသွားတဲ့အခါ ဒီ method အလုပ်လုပ်ပါတယ်။
        ဒီနေရာမှာ many-to-many relationship တွေကို သတ်မှတ်နိုင်ပါတယ်။
        """
        user = super().save_user(request, sociallogin, form)
        if hasattr(user, 'add_role'):
            if not user.is_superuser and not user.is_staff:
                user.add_role('student') # type: ignore
        return user

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request, sociallogin=None):
        return getattr(settings, 'ACCOUNT_ALLOW_REGISTRATION', True)
