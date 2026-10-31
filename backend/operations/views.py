from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response

from companies.permissions import lead_projects
from companies.viewsets import CompanyScopedViewSet
from core.services import record_event
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
from operations.serializers import (
    DurationUnitSerializer,
    KindReorderSerializer,
    ProjectScopeSerializer,
    SheetCellSerializer,
    SheetColumnSerializer,
    SheetTextCellSerializer,
    SiteReportSerializer,
    WorkKindSerializer,
    WorkMeasureSerializer,
    WorkplaceSerializer,
    WorkplaceTeamSerializer,
    WorkTypeCategorySerializer,
    WorkTypeSerializer,
)
from operations.services import (
    create_workplace,
    find_sheet_report,
    resolve_sheet_column,
    upsert_sheet_cell,
    upsert_sheet_text,
    reorder_duration_units,
    reorder_sheet_columns,
    reorder_kinds,
    reorder_work_categories,
    sync_workplace_location,
)


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
    return queryset.select_related("work_type__category", "work_type__measure", "length_unit").prefetch_related(
        "scopes__work_type__measure"
    ).annotate(
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
    lead_actions = ("sheet",)

    def scope_for_lead(self, queryset):
        return queryset.filter(pk__in=lead_projects(self.request).values("pk"))

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
        scopes = workplace.scopes.select_related("work_type__category", "work_type__measure", "length_unit")
        data["scopes"] = ProjectScopeSerializer(scopes, many=True, context={"request": request}).data
        columns = workplace.sheet_columns.select_related("scope__work_type__measure", "team")
        data["sheet_columns"] = SheetColumnSerializer(columns, many=True, context={"request": request}).data
        texts = SheetTextCell.objects.filter(column__workplace=workplace)
        data["sheet_texts"] = SheetTextCellSerializer(texts, many=True, context={"request": request}).data
        return Response(data)

    @action(detail=True, methods=["post"])
    def sheet(self, request, pk=None):
        workplace = self.get_object()
        serializer = SheetCellSerializer(data=request.data, context={"request": request, "workplace": workplace})
        serializer.is_valid(raise_exception=True)
        column = serializer.validated_data["column"]
        work_date = serializer.validated_data["work_date"]
        if column.kind == SheetColumn.Kind.TEXT:
            cell = upsert_sheet_text(
                column=column,
                work_date=work_date,
                text=serializer.validated_data.get("text", ""),
            )
            if cell is None:
                return Response({"deleted": True, "kind": "text"})
            return Response(SheetTextCellSerializer(cell, context={"request": request}).data)
        team, scope = resolve_sheet_column(
            column,
            workplace,
            team=serializer.validated_data.get("team"),
            scope=serializer.validated_data.get("scope"),
        )
        existing = find_sheet_report(workplace, team, work_date, scope)
        report = upsert_sheet_cell(
            workplace=workplace,
            team=team,
            work_date=work_date,
            scope=scope,
            quantity=serializer.validated_data.get("quantity"),
            note=serializer.validated_data.get("note", ""),
        )
        if report is None:
            if existing is not None:
                record_event(
                    request,
                    "report.deleted",
                    existing,
                    project=workplace,
                    data={"work_date": str(existing.work_date)},
                )
            return Response({"deleted": True, "kind": column.kind})
        record_event(
            request,
            "report.updated" if existing is not None else "report.created",
            report,
            project=workplace,
            data={"work_date": str(report.work_date), "quantity": str(report.quantity)},
        )
        return Response(SiteReportSerializer(report, context={"request": request}).data)


class WorkplaceTeamViewSet(CompanyScopedViewSet):
    serializer_class = WorkplaceTeamSerializer
    queryset = WorkplaceTeam.objects.select_related("workplace", "team__lead_user")
    company_lookup = "workplace__company"

    def scope_for_lead(self, queryset):
        return queryset.filter(workplace__in=lead_projects(self.request).values("pk"))

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        team_id = self.request.query_params.get("team")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        return queryset


class DurationUnitViewSet(CompanyScopedViewSet):
    serializer_class = DurationUnitSerializer
    queryset = DurationUnit.objects.all()
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = KindReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        units = reorder_duration_units(request.company, serializer.validated_data["ids"])
        return Response(DurationUnitSerializer(units, many=True, context={"request": request}).data)


class SheetColumnViewSet(CompanyScopedViewSet):
    serializer_class = SheetColumnSerializer
    queryset = SheetColumn.objects.select_related("workplace", "scope__work_type__measure", "team")
    company_lookup = "workplace__company"
    pagination_class = None

    def scope_for_lead(self, queryset):
        return queryset.filter(workplace__in=lead_projects(self.request).values("pk"))

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        return queryset

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = KindReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workplace_id = request.data.get("workplace") or request.query_params.get("workplace")
        workplace = Workplace.objects.filter(pk=workplace_id, company=request.company).first()
        if workplace is None:
            return Response({"workplace": "Choose a project."}, status=400)
        columns = reorder_sheet_columns(workplace, serializer.validated_data["ids"])
        return Response(SheetColumnSerializer(columns, many=True, context={"request": request}).data)


class ProjectScopeViewSet(CompanyScopedViewSet):
    serializer_class = ProjectScopeSerializer
    queryset = ProjectScope.objects.select_related(
        "workplace",
        "work_type__category",
        "work_type__measure",
        "length_unit",
    )
    company_lookup = "workplace__company"

    def scope_for_lead(self, queryset):
        return queryset.filter(workplace__in=lead_projects(self.request).values("pk"))

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        return queryset


class WorkKindViewSet(CompanyScopedViewSet):
    serializer_class = WorkKindSerializer
    queryset = WorkKind.objects.all()
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = KindReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kinds = reorder_kinds(request.company, serializer.validated_data["ids"])
        return Response(WorkKindSerializer(kinds, many=True, context={"request": request}).data)


class WorkMeasureViewSet(CompanyScopedViewSet):
    serializer_class = WorkMeasureSerializer
    queryset = WorkMeasure.objects.select_related("kind")


class WorkTypeCategoryViewSet(CompanyScopedViewSet):
    serializer_class = WorkTypeCategorySerializer
    queryset = WorkTypeCategory.objects.all()
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = KindReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        categories = reorder_work_categories(request.company, serializer.validated_data["ids"])
        return Response(WorkTypeCategorySerializer(categories, many=True, context={"request": request}).data)


class WorkTypeViewSet(CompanyScopedViewSet):
    serializer_class = WorkTypeSerializer
    queryset = WorkType.objects.select_related("category", "measure__kind")


class SiteReportViewSet(CompanyScopedViewSet):
    serializer_class = SiteReportSerializer
    queryset = SiteReport.objects.select_related(
        "workplace__work_type__measure",
        "team",
        "task__work_type__measure",
        "scope__work_type__measure",
    )
    company_lookup = "workplace__company"
    lead_actions = ("create", "update", "partial_update")

    def scope_for_lead(self, queryset):
        return queryset.filter(workplace__in=lead_projects(self.request).values("pk"))

    def get_queryset(self):
        queryset = super().get_queryset()
        workplace_id = self.request.query_params.get("workplace")
        if workplace_id:
            queryset = queryset.filter(workplace_id=workplace_id)
        task_id = self.request.query_params.get("task")
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset

    def perform_create(self, serializer):
        report = serializer.save()
        record_event(
            self.request,
            "report.created",
            report,
            project=report.workplace,
            data={"work_date": str(report.work_date), "quantity": str(report.quantity)},
        )

    def perform_update(self, serializer):
        report = serializer.save()
        record_event(
            self.request,
            "report.updated",
            report,
            project=report.workplace,
            data={"work_date": str(report.work_date), "quantity": str(report.quantity)},
        )
