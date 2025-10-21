# api/auth_serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class LoxaTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Example claims:
        token["email"] = user.email
        token["username"] = user.get_username()
        # token["org_ids"] = list(user.orgmembership_set.values_list("org_id", flat=True))
        return token
