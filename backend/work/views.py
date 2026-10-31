from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response

from companies.permissions import is_team_lead, lead_projects
from companies.viewsets import CompanyScopedViewSet
from core.serializers import ActivityEventSerializer
from core.services import events_for, record_event
from operations.models import SiteReport
from work.models import Task, TaskCategory, TaskComment, TaskPhase, TaskStatus
from work.serializers import (
    StatusReorderSerializer,
    TaskCategorySerializer,
    TaskCommentSerializer,
    TaskMoveSerializer,
    TaskPhaseSerializer,
    TaskSerializer,
    TaskStatusSerializer,
)
from work.services import create_task, move_task, reorder_categories, reorder_phases, reorder_statuses

TRACKED_FIELDS = (
    "title",
    "description",
    "priority",
    "phase_id",
    "team_id",
    "assignee_user_id",
    "start_date",
    "due_date",
    "planned_quantity",
    "status_id",
    "work_type_id",
)


def _with_progress(queryset):
    done = (
        SiteReport.objects.filter(task=OuterRef("pk"))
        .values("task")
        .annotate(total=Sum("quantity"))
        .values("total")
    )
    return queryset.select_related(
        "project__work_type__measure",
        "status__category",
        "phase",
        "work_type__measure",
        "team",
        "assignee_user",
        "created_by",
    ).annotate(
        done_quantity=Coalesce(
            Subquery(done, output_field=DecimalField(max_digits=12, decimal_places=2)),
            Decimal("0.00"),
        )
    )


class TaskCategoryViewSet(CompanyScopedViewSet):
    serializer_class = TaskCategorySerializer
    queryset = TaskCategory.objects.all()
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = StatusReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        categories = reorder_categories(request.company, serializer.validated_data["ids"])
        return Response(TaskCategorySerializer(categories, many=True, context={"request": request}).data)


class TaskPhaseViewSet(CompanyScopedViewSet):
    serializer_class = TaskPhaseSerializer
    queryset = TaskPhase.objects.all()
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = StatusReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phases = reorder_phases(request.company, serializer.validated_data["ids"])
        return Response(TaskPhaseSerializer(phases, many=True, context={"request": request}).data)


class TaskStatusViewSet(CompanyScopedViewSet):
    serializer_class = TaskStatusSerializer
    queryset = TaskStatus.objects.select_related("category")
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = StatusReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        statuses = reorder_statuses(request.company, serializer.validated_data["ids"])
        return Response(TaskStatusSerializer(statuses, many=True, context={"request": request}).data)


class TaskViewSet(CompanyScopedViewSet):
    serializer_class = TaskSerializer
    queryset = _with_progress(Task.objects.all())
    lead_actions = ("move", "comments")

    def scope_for_lead(self, queryset):
        return queryset.filter(project__in=lead_projects(self.request).values("pk"))

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        for param, lookup in (
            ("project", "project_id"),
            ("status", "status_id"),
            ("team", "team_id"),
            ("phase", "phase_id"),
            ("priority", "priority"),
        ):
            value = params.get(param)
            if value:
                queryset = queryset.filter(**{lookup: value})
        search = params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def _reload(self, task):
        return _with_progress(Task.objects.filter(pk=task.pk)).get()

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        project = data.pop("project")
        task = create_task(self.request.company, project, self.request.user, **data)
        record_event(self.request, "task.created", task, project=project, data={"title": task.title})
        serializer.instance = self._reload(task)

    def perform_update(self, serializer):
        before = {field: getattr(serializer.instance, field) for field in TRACKED_FIELDS}
        task = serializer.save()
        changes = {
            field.removesuffix("_id"): {"from": str(before[field]), "to": str(getattr(task, field))}
            for field in TRACKED_FIELDS
            if before[field] != getattr(task, field)
        }
        if changes:
            record_event(self.request, "task.updated", task, project=task.project, data=changes)
        serializer.instance = self._reload(task)

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        task = self.get_object()
        if is_team_lead(request) and (task.team is None or task.team.lead_user_id != request.user.id):
            return Response(
                {"detail": "You can only move tasks assigned to a team you lead."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        serializer = TaskMoveSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        old_status = task.status
        new_status = serializer.validated_data["status"]
        move_task(task, new_status, serializer.validated_data["position"])
        if old_status.pk != new_status.pk:
            record_event(
                request,
                "task.moved",
                task,
                project=task.project,
                data={"from": old_status.name, "to": new_status.name},
            )
        return Response(self.get_serializer(self._reload(task)).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            comments = task.comments.select_related("author")
            return Response(TaskCommentSerializer(comments, many=True).data)
        if is_team_lead(request) and (task.team is None or task.team.lead_user_id != request.user.id):
            return Response(
                {"detail": "You can only comment on tasks assigned to a team you lead."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = TaskComment.objects.create(task=task, author=request.user, body=serializer.validated_data["body"])
        record_event(request, "task.commented", task, project=task.project, data={"body": comment.body[:200]})
        return Response(TaskCommentSerializer(comment).data, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        task = self.get_object()
        return Response(ActivityEventSerializer(events_for(task, request.company), many=True).data)
