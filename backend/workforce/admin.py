from django.contrib import admin

from workforce.models import Team, Worker, WorkerType


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "status", "worker_type", "team"]
    list_filter = ["status", "company"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "company", "worker_count", "lead_note", "lead_user"]


admin.site.register(WorkerType)
