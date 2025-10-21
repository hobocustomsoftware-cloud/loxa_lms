# accounts/jwt.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class OrgTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # user သည် ဘယ် org အတွင်းက member လဲ (ManyToMany/through table မူတည်)
        org_ids = list(user.memberships.values_list("org_id", flat=True)) if hasattr(user,"memberships") else []
        token["org_ids"] = org_ids
        return token
