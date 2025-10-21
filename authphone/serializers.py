from rest_framework import serializers

class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code  = serializers.CharField(max_length=6)
