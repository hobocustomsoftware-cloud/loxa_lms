from rest_framework import serializers


class AgoraTokenRequestSer(serializers.Serializer):
    channel = serializers.CharField(max_length=200)
    role = serializers.ChoiceField(choices=["publisher", "subscriber"], default="subscriber")
    ttl = serializers.IntegerField(required=False, min_value=60, max_value=24 * 3600)


class AgoraTokenResponseSer(serializers.Serializer):
    app_id = serializers.CharField(required=False, allow_blank=True)
    channel = serializers.CharField()
    uid = serializers.CharField()
    token = serializers.CharField(required=False)
    rtc_token = serializers.CharField()
    rtm_token = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False)
    expires_in = serializers.IntegerField()
    expire_at = serializers.IntegerField(required=False)
