from django.contrib import admin

from work.models import Task, TaskCategory, TaskComment, TaskPhase, TaskStatus


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["number", "title", "project", "status", "priority", "phase", "team", "due_date"]
    list_filter = ["company", "status", "phase", "priority"]


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "color", "position"]


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "category", "position"]


@admin.register(TaskPhase)
class TaskPhaseAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "position"]


admin.site.register(TaskComment)
