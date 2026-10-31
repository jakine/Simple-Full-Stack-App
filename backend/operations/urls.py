from rest_framework.routers import DefaultRouter

from operations.views import (
    SiteReportViewSet,
    WorkMeasureViewSet,
    WorkplaceTeamViewSet,
    WorkplaceViewSet,
    WorkTypeViewSet,
)

router = DefaultRouter()
router.register("workplaces", WorkplaceViewSet, basename="workplace")
router.register("workplace-teams", WorkplaceTeamViewSet, basename="workplace-team")
router.register("work-measures", WorkMeasureViewSet, basename="work-measure")
router.register("work-types", WorkTypeViewSet, basename="work-type")
router.register("site-reports", SiteReportViewSet, basename="site-report")

urlpatterns = router.urls
