from django.contrib import admin

from core.models import ActivityEvent


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ["created_at", "company", "actor", "verb", "target_type", "target_id", "project"]
    list_filter = ["company", "verb"]
