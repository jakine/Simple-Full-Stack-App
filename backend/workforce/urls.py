from rest_framework.routers import DefaultRouter

from workforce.views import TeamViewSet, WorkerTypeViewSet, WorkerViewSet

router = DefaultRouter()
router.register("worker-types", WorkerTypeViewSet, basename="worker-type")
router.register("teams", TeamViewSet, basename="team")
router.register("workers", WorkerViewSet, basename="worker")

urlpatterns = router.urls
