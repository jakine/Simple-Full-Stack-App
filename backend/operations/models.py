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
    length_unit = models.CharField(
        max_length=10,
        blank=True,
        choices=[("day", "Days"), ("week", "Weeks"), ("month", "Months")],
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


class WorkMeasure(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="work_measures",
    )
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=20)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_work_measure_name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class WorkType(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
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

    def __str__(self):
        return f"{self.workplace} {self.work_date}"
