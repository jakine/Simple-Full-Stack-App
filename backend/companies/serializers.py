from rest_framework import serializers

from companies.models import Membership


class CompanyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source="user_id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "email", "role"]


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)


class SwitchSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
