from django.conf import settings
from django.db import models


class ActivityEvent(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="activity_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_events",
    )
    project = models.ForeignKey(
        "operations.Workplace",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activity_events",
    )
    verb = models.CharField(max_length=60)
    target_type = models.CharField(max_length=60)
    target_id = models.PositiveBigIntegerField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["company", "target_type", "target_id"]),
            models.Index(fields=["project", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.verb} {self.target_type}#{self.target_id}"
