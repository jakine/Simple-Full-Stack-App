from rest_framework import serializers

from core.models import ActivityEvent


class ActivityEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project.name", read_only=True, allow_null=True)

    class Meta:
        model = ActivityEvent
        fields = [
            "id",
            "actor",
            "actor_email",
            "project",
            "project_name",
            "verb",
            "target_type",
            "target_id",
            "data",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_email(self, obj):
        return obj.actor.email if obj.actor_id else ""
