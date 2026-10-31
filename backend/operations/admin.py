from django.contrib import admin

from operations.models import SiteReport, WorkMeasure, Workplace, WorkplaceTeam, WorkType

admin.site.register(Workplace)
admin.site.register(WorkplaceTeam)
admin.site.register(WorkMeasure)
admin.site.register(WorkType)
admin.site.register(SiteReport)
