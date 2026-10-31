from rest_framework.routers import DefaultRouter

from work.views import TaskCategoryViewSet, TaskPhaseViewSet, TaskStatusViewSet, TaskViewSet

router = DefaultRouter()
router.register("task-categories", TaskCategoryViewSet, basename="task-category")
router.register("task-phases", TaskPhaseViewSet, basename="task-phase")
router.register("task-statuses", TaskStatusViewSet, basename="task-status")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = router.urls
