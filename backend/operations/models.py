from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Workplace(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="workplaces",
    )
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    length_count = models.PositiveIntegerField(null=True, blank=True)
    length_unit = models.ForeignKey(
        "DurationUnit",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="workplaces",
    )
    work_type = models.ForeignKey(
        "WorkType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="workplaces",
    )
    planned_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkplaceTeam(models.Model):
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        related_name="workplace_teams",
    )
    team = models.ForeignKey(
        "workforce.Team",
        on_delete=models.CASCADE,
        related_name="workplace_assignments",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["team__name", "-start_date"]

    def __str__(self):
        return f"{self.team} @ {self.workplace}"


class DurationUnit(models.Model):
    class TimelineStep(models.TextChoices):
        DAY = "day", "Day"
        WEEK = "week", "Week"
        MONTH = "month", "Month"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="duration_units",
    )
    name = models.CharField(max_length=60)
    symbol = models.CharField(max_length=20)
    days_per_unit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    timeline_step = models.CharField(max_length=10, blank=True, choices=TimelineStep.choices)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_duration_unit_name"),
        ]

    def __str__(self):
        return self.name


class ProjectScope(models.Model):
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        related_name="scopes",
    )
    work_type = models.ForeignKey(
        "WorkType",
        on_delete=models.PROTECT,
        related_name="scopes",
    )
    planned_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    length_count = models.PositiveIntegerField(null=True, blank=True)
    length_unit = models.ForeignKey(
        DurationUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="scopes",
    )
    teams_needed = models.PositiveIntegerField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["workplace", "work_type"], name="unique_scope_work_type_per_project"),
        ]

    def __str__(self):
        return f"{self.work_type} @ {self.workplace}"


class WorkKind(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="work_kinds",
    )
    name = models.CharField(max_length=60)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_work_kind_name"),
        ]

    def __str__(self):
        return self.name


class WorkMeasure(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="work_measures",
    )
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=20)
    kind = models.ForeignKey(WorkKind, on_delete=models.PROTECT, related_name="measures")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_work_measure_name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class WorkTypeCategory(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="work_type_categories",
    )
    name = models.CharField(max_length=60)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_work_type_category_name"),
        ]

    def __str__(self):
        return self.name


class WorkType(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="work_types",
    )
    category = models.ForeignKey(
        WorkTypeCategory,
        on_delete=models.PROTECT,
        related_name="work_types",
    )
    measure = models.ForeignKey(
        WorkMeasure,
        on_delete=models.PROTECT,
        related_name="work_types",
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_work_type_name"),
        ]

    def __str__(self):
        return self.name


class SiteReport(models.Model):
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    team = models.ForeignKey(
        "workforce.Team",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_reports",
    )
    task = models.ForeignKey(
        "work.Task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    scope = models.ForeignKey(
        "ProjectScope",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    work_date = models.DateField()
    days = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    note = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-work_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["workplace", "team", "work_date", "scope"],
                name="unique_report_team_date_scope",
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        return f"{self.workplace} {self.work_date}"


class SheetColumn(models.Model):
    class Kind(models.TextChoices):
        WORK_TYPE = "work_type", "Work type"
        TEAM = "team", "Team"
        TEXT = "text", "Text"

    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        related_name="sheet_columns",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=120, blank=True)
    scope = models.ForeignKey(
        ProjectScope,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sheet_columns",
    )
    team = models.ForeignKey(
        "workforce.Team",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sheet_columns",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.name or f"{self.kind} @ {self.workplace}"


class SheetTextCell(models.Model):
    column = models.ForeignKey(
        SheetColumn,
        on_delete=models.CASCADE,
        related_name="text_cells",
    )
    work_date = models.DateField()
    text = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["work_date", "id"]
        constraints = [
            models.UniqueConstraint(fields=["column", "work_date"], name="unique_sheet_text_cell"),
        ]

    def __str__(self):
        return f"{self.column} {self.work_date}"
