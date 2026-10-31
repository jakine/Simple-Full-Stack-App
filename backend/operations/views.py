from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from rest_framework.response import Response

from companies.viewsets import CompanyScopedViewSet
from operations.models import SiteReport, WorkMeasure, Workplace, WorkplaceTeam, WorkType
from operations.serializers import (
    SiteReportSerializer,
    WorkMeasureSerializer,
    WorkplaceSerializer,
    WorkplaceTeamSerializer,
    WorkTypeSerializer,
)
from operations.services import create_workplace, sync_workplace_location


def _with_progress(queryset):
    done = (
        SiteReport.objects.filter(workplace=OuterRef("pk"))
        .values("workplace")
        .annotate(total=Sum("quantity"))
        .values("total")
    )
    days = (
        SiteReport.objects.filter(workplace=OuterRef("pk"))
        .values("workplace")
        .annotate(total=Sum("days"))
        .values("total")
    )
    return queryset.select_related("work_type__measure").annotate(
        done_quantity=Coalesce(
            Subquery(done, output_field=DecimalField(max_digits=12, decimal_places=2)),
            Decimal("0.00"),
        ),
        days_worked=Coalesce(
            Subquery(days, output_field=DecimalField(max_digits=8, decimal_places=2)),
            Decimal("0.00"),
        ),
    )


class WorkplaceViewSet(CompanyScopedViewSet):
    serializer_class = WorkplaceSerializer
    queryset = _with_progress(Workplace.objects.all())

    def perform_create(self, serializer):
        workplace = create_workplace(self.request.company, **serializer.validated_data)
        serializer.instance = _with_progress(Workplace.objects.filter(pk=workplace.pk)).get()

    def perform_update(self, serializer):
        workplace = serializer.save()
        sync_workplace_location(workplace)
        serializer.instance = _with_progress(Workplace.objects.filter(pk=workplace.pk)).get()

    def retrieve(self, request, *args, **kwargs):
        workplace = self.get_object()
        data = self.get_serializer(workplace).data
        teams = workplace.workplace_teams.select_related("team__lead_user", "workplace")
        data["teams"] = WorkplaceTeamSerializer(teams, many=True, context={"request": request}).data
        return Response(data)


class WorkplaceTeamViewSet(CompanyScopedViewSet):
    serializer_class = WorkplaceTeamSerializer
    queryset = WorkplaceTeam.objects.select_related("workplace", "team__lead_user")
    company_lookup = "workplace__company"

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        team_id = self.request.query_params.get("team")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        return queryset


class WorkMeasureViewSet(CompanyScopedViewSet):
    serializer_class = WorkMeasureSerializer
    queryset = WorkMeasure.objects.all()


class WorkTypeViewSet(CompanyScopedViewSet):
    serializer_class = WorkTypeSerializer
    queryset = WorkType.objects.select_related("measure")


class SiteReportViewSet(CompanyScopedViewSet):
    serializer_class = SiteReportSerializer
    queryset = SiteReport.objects.select_related("workplace__work_type__measure", "team")
    company_lookup = "workplace__company"

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        return queryset
