from rest_framework.routers import DefaultRouter

from core.views import ActivityEventViewSet

router = DefaultRouter()
router.register("activity", ActivityEventViewSet, basename="activity")

urlpatterns = router.urls
