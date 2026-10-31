from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from companies.permissions import HasCompanyRole, is_team_lead, lead_projects
from core.models import ActivityEvent
from core.serializers import ActivityEventSerializer


class ActivityEventViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, HasCompanyRole]
    serializer_class = ActivityEventSerializer

    def get_queryset(self):
        queryset = ActivityEvent.objects.filter(company=self.request.company).select_related("actor", "project")
        if is_team_lead(self.request):
            queryset = queryset.filter(project__in=lead_projects(self.request).values("pk"))
        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
