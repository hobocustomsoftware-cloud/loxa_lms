from rest_framework import serializers

class AgoraTokenRequestSer(serializers.Serializer):
    channel = serializers.CharField(max_length=200)
    role = serializers.ChoiceField(choices=["publisher", "subscriber"], default="subscriber")
    ttl = serializers.IntegerField(required=False, min_value=60, max_value=24*3600)

class AgoraTokenResponseSer(serializers.Serializer):
    channel = serializers.CharField()
    uid = serializers.CharField()
    rtc_token = serializers.CharField()
    rtm_token = serializers.CharField()
    expires_in = serializers.IntegerField()
