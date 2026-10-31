from companies.viewsets import CompanyScopedViewSet
from workforce.models import Team, Worker, WorkerType
from workforce.serializers import TeamSerializer, WorkerSerializer, WorkerTypeSerializer


class WorkerTypeViewSet(CompanyScopedViewSet):
    serializer_class = WorkerTypeSerializer
    queryset = WorkerType.objects.all()


class TeamViewSet(CompanyScopedViewSet):
    serializer_class = TeamSerializer
    queryset = Team.objects.select_related("lead_user")


class WorkerViewSet(CompanyScopedViewSet):
    serializer_class = WorkerSerializer
    queryset = Worker.objects.select_related("team", "worker_type")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
