from django.db import transaction
from django.db.models import Max

from operations.models import Workplace
from work.models import Task, TaskCategory, TaskPhase, TaskStatus

DEFAULT_CATEGORIES = (
    ("To do", "#8a9696"),
    ("In progress", "#01696f"),
    ("Done", "#2e7d32"),
)

DEFAULT_PHASES = ("Design", "Preconstruction", "Procurement", "Execution", "Post construction")

DEFAULT_STATUSES = (
    ("To do", "To do"),
    ("In progress", "In progress"),
    ("Inspection", "In progress"),
    ("Done", "Done"),
)


def create_default_categories(company):
    return [
        TaskCategory.objects.get_or_create(
            company=company,
            name=name,
            defaults={"color": color, "position": position},
        )[0]
        for position, (name, color) in enumerate(DEFAULT_CATEGORIES)
    ]


def create_default_phases(company):
    return [
        TaskPhase.objects.get_or_create(
            company=company,
            name=name,
            defaults={"position": position},
        )[0]
        for position, name in enumerate(DEFAULT_PHASES)
    ]


def default_task_phase(company):
    create_default_phases(company)
    return TaskPhase.objects.get(company=company, name="Execution")


def reorder_phases(company, ids):
    phases = {phase.pk: phase for phase in TaskPhase.objects.filter(company=company)}
    ordered = [phases[phase_id] for phase_id in ids if phase_id in phases]
    seen = {phase.pk for phase in ordered}
    ordered.extend(phase for phase in TaskPhase.objects.filter(company=company) if phase.pk not in seen)
    with transaction.atomic():
        for index, phase in enumerate(ordered):
            if phase.position != index:
                phase.position = index
                phase.save(update_fields=["position"])
    return TaskPhase.objects.filter(company=company)


def create_default_statuses(company):
    categories = {category.name: category for category in create_default_categories(company)}
    return [
        TaskStatus.objects.get_or_create(
            company=company,
            name=name,
            defaults={"category": categories[category_name], "position": position},
        )[0]
        for position, (name, category_name) in enumerate(DEFAULT_STATUSES)
    ]


def create_task(company, project, created_by, **fields):
    with transaction.atomic():
        Workplace.objects.select_for_update().filter(pk=project.pk).first()
        last = Task.objects.filter(project=project).aggregate(top=Max("number"))["top"] or 0
        if "status" not in fields or fields["status"] is None:
            fields["status"] = (
                TaskStatus.objects.filter(company=company).first() or create_default_statuses(company)[0]
            )
        if "phase" not in fields or fields["phase"] is None:
            fields["phase"] = default_task_phase(company)
        column_end = Task.objects.filter(project=project, status=fields["status"]).aggregate(
            top=Max("position")
        )["top"]
        fields.setdefault("position", 0 if column_end is None else column_end + 1)
        return Task.objects.create(
            company=company,
            project=project,
            number=last + 1,
            created_by=created_by,
            **fields,
        )


def move_task(task, status, position):
    with transaction.atomic():
        column = list(
            Task.objects.select_for_update()
            .filter(project=task.project, status=status)
            .exclude(pk=task.pk)
            .order_by("position", "id")
        )
        position = max(0, min(position, len(column)))
        task.status = status
        column.insert(position, task)
        for index, row in enumerate(column):
            if row.pk == task.pk:
                row.position = index
                row.save(update_fields=["status", "position", "updated_at"])
            elif row.position != index:
                row.position = index
                row.save(update_fields=["position"])
    return task


def reorder_statuses(company, ids):
    statuses = {status.pk: status for status in TaskStatus.objects.filter(company=company)}
    ordered = [statuses[status_id] for status_id in ids if status_id in statuses]
    seen = {status.pk for status in ordered}
    ordered.extend(status for status in TaskStatus.objects.filter(company=company) if status.pk not in seen)
    with transaction.atomic():
        for index, status in enumerate(ordered):
            if status.position != index:
                status.position = index
                status.save(update_fields=["position"])
    return TaskStatus.objects.filter(company=company).select_related("category")


def reorder_categories(company, ids):
    categories = {category.pk: category for category in TaskCategory.objects.filter(company=company)}
    ordered = [categories[category_id] for category_id in ids if category_id in categories]
    seen = {category.pk for category in ordered}
    ordered.extend(category for category in TaskCategory.objects.filter(company=company) if category.pk not in seen)
    with transaction.atomic():
        for index, category in enumerate(ordered):
            if category.position != index:
                category.position = index
                category.save(update_fields=["position"])
    return TaskCategory.objects.filter(company=company)
