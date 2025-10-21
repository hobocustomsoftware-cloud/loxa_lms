from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import  User
from django.utils.crypto import get_random_string

User = get_user_model()

class PhoneRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user( # type: ignore
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
        ) # type: ignore
        return user


class PhoneLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)




# class RequestOTPSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()

#     def create(self, validated_data):
#         phone = validated_data["phone_number"]
#         # generate 6 digit
#         code = get_random_string(6, allowed_chars="0123456789")
#         PhoneOTP.objects.create(phone_number=phone, code=code)
#         # TODO: integrate SMS provider here (e.g., Twilio, local SMS gateway)
#         print(f"DEBUG OTP for {phone} = {code}")  # console for dev
#         return {"phone_number": phone}


# class VerifyOTPSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     code = serializers.CharField(max_length=6)

#     def validate(self, attrs):
#         phone = attrs["phone_number"]
#         code = attrs["code"]
#         try:
#             otp = PhoneOTP.objects.filter(phone_number=phone).latest("created_at")
#         except PhoneOTP.DoesNotExist:
#             raise serializers.ValidationError("OTP not requested")

#         if not otp.is_valid():
#             raise serializers.ValidationError("OTP expired")
#         if otp.code != code:
#             raise serializers.ValidationError("Invalid code")
#         attrs["otp"] = otp
#         return attrs

#     def create(self, validated_data):
#         phone = validated_data["phone_number"]

#         user, _ = User.objects.get_or_create(
#             phone_number=phone,
#             defaults={"email": f"{phone}@autogen.local", "is_active": True}
#         )

#         from rest_framework_simplejwt.tokens import RefreshToken
#         refresh = RefreshToken.for_user(user)
#         return {
#             "refresh": str(refresh),
#             "access": str(refresh.access_token),
#             "user_id": user.id, # type: ignore
#             "phone_number": user.phone_number
#         }



from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import OrganizationMembership, OrgRole
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

class OrgMembershipMiniSer(serializers.ModelSerializer):
    orgId   = serializers.IntegerField(source="org.id", read_only=True)
    orgName = serializers.CharField(source="org.name", read_only=True)
    orgSlug = serializers.CharField(source="org.slug", read_only=True)

    class Meta:
        model  = OrganizationMembership
        fields = ("orgId", "orgName", "orgSlug", "role")

class MeSerializer(serializers.ModelSerializer):
    # server-side boolean flags (existing)
    isStaff      = serializers.BooleanField(source="is_staff", read_only=True)
    isSuperuser  = serializers.BooleanField(source="is_superuser", read_only=True)
    isAdmin      = serializers.SerializerMethodField()
    isEditor     = serializers.SerializerMethodField()
    picture      = serializers.SerializerMethodField()
    isModerator  = serializers.SerializerMethodField()

    # ✅ NEW: global roles (slug list)
    roles        = serializers.SerializerMethodField()

    # ✅ NEW: org memberships (for student/teacher/parent)
    orgs         = serializers.SerializerMethodField()
    # optional: active org role if you use org middleware
    activeOrgRole = serializers.SerializerMethodField()

    # ✅ NEW: abilities used by Flutter UI
    canHostLive  = serializers.SerializerMethodField()
    canJoinLive  = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = (
            "id","email","first_name","last_name", "picture",
            "isStaff","isSuperuser","isAdmin","isEditor","isModerator",
            "roles","orgs","activeOrgRole",
            "canHostLive","canJoinLive",
        )

    # ---- role/flag resolvers ----
    def get_isAdmin(self, obj):     return obj.is_admin
    def get_isEditor(self, obj):    return obj.is_editor
    def get_isModerator(self, obj): return obj.is_moderator

    def get_picture(self, obj: User) -> str | None:
        """
        Get user's profile picture URL from their social account.
        """
        try:
            social_account = SocialAccount.objects.filter(user=obj).first()
            return social_account.get_avatar_url() if social_account else None
        except (ImportError, AttributeError, SocialAccount.DoesNotExist):
            return None

    def get_roles(self, obj):
        # Role M2M + fallback to Group names
        slugs = set(obj.roles.values_list("slug", flat=True))
        slugs.update(obj.groups.values_list("name", flat=True))
        # normalize (only the ones we care)
        wanted = {"super_admin","admin","editor","moderator","teacher","student","parent"}
        return sorted(list(slugs & wanted))

    def get_orgs(self, obj):
        qs = OrganizationMembership.objects.filter(user=obj).select_related("org")
        return OrgMembershipMiniSer(qs, many=True).data

    def get_activeOrgRole(self, obj):
        request = self.context.get("request")
        org = getattr(request, "org", None)
        if not org:
            return None
        m = OrganizationMembership.objects.filter(org=org, user=obj).only("role").first()
        return m.role if m else None

    def get_canHostLive(self, obj):
        # admin / teacher / moderator can host
        return (
            obj.is_admin
            or obj.roles.filter(slug__in=["teacher","moderator"]).exists()
            or obj.groups.filter(name__in=["teacher","moderator"]).exists()
        )

    def get_canJoinLive(self, obj):
        # logged-in + any of these roles
        return True  # already authenticated endpoint; keep simple
