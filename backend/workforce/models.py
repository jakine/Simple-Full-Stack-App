from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class WorkerType(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="worker_types",
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_worker_type_name"),
        ]

    def __str__(self):
        return self.name


class Team(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="teams",
    )
    number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    name = models.CharField(max_length=200)
    worker_count = models.PositiveIntegerField(default=0)
    lead_note = models.CharField(max_length=300, blank=True)
    lead_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="led_teams",
    )

    class Meta:
        ordering = ["number", "name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_team_name"),
            models.UniqueConstraint(fields=["company", "number"], name="unique_team_number"),
        ]

    def __str__(self):
        return f"{self.number} {self.name}"


class Worker(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="workers",
    )
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    worker_type = models.ForeignKey(
        WorkerType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="workers",
    )
    team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
