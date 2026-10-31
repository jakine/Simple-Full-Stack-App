from django.contrib import admin

from operations.models import (
    DurationUnit,
    ProjectScope,
    SheetColumn,
    SheetTextCell,
    SiteReport,
    WorkKind,
    WorkMeasure,
    Workplace,
    WorkplaceTeam,
    WorkType,
    WorkTypeCategory,
)

admin.site.register(Workplace)
admin.site.register(WorkplaceTeam)
admin.site.register(DurationUnit)
admin.site.register(ProjectScope)
admin.site.register(WorkKind)
admin.site.register(WorkMeasure)
admin.site.register(WorkTypeCategory)
admin.site.register(WorkType)
admin.site.register(SiteReport)
admin.site.register(SheetColumn)
admin.site.register(SheetTextCell)
