from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

DEFAULT_UNITS = (
    ("Day", "day", Decimal("1.00"), "day", 0),
    ("Week", "week", Decimal("7.00"), "week", 1),
    ("Month", "month", Decimal("30.00"), "month", 2),
)


def add_units_and_scopes(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    DurationUnit = apps.get_model("operations", "DurationUnit")
    Workplace = apps.get_model("operations", "Workplace")
    ProjectScope = apps.get_model("operations", "ProjectScope")
    for company in Company.objects.all():
        by_symbol = {}
        for name, symbol, days, step, position in DEFAULT_UNITS:
            by_symbol[symbol] = DurationUnit.objects.create(
                company=company,
                name=name,
                symbol=symbol,
                days_per_unit=days,
                timeline_step=step,
                position=position,
            )
        for workplace in Workplace.objects.filter(company=company):
            slug = workplace.length_unit_slug
            workplace.length_unit = by_symbol.get(slug)
            workplace.save(update_fields=["length_unit"])
            if workplace.work_type_id and workplace.planned_quantity:
                ProjectScope.objects.create(
                    workplace=workplace,
                    work_type_id=workplace.work_type_id,
                    planned_quantity=workplace.planned_quantity,
                    length_count=workplace.length_count,
                    length_unit=workplace.length_unit,
                    position=0,
                )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("operations", "0011_work_type_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="DurationUnit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("symbol", models.CharField(max_length=20)),
                (
                    "days_per_unit",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                (
                    "timeline_step",
                    models.CharField(
                        blank=True,
                        choices=[("day", "Day"), ("week", "Week"), ("month", "Month")],
                        max_length=10,
                    ),
                ),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="duration_units",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="durationunit",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_duration_unit_name"),
        ),
        migrations.RenameField(
            model_name="workplace",
            old_name="length_unit",
            new_name="length_unit_slug",
        ),
        migrations.AddField(
            model_name="workplace",
            name="length_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="workplaces",
                to="operations.durationunit",
            ),
        ),
        migrations.CreateModel(
            name="ProjectScope",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "planned_quantity",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                ("length_count", models.PositiveIntegerField(blank=True, null=True)),
                ("teams_needed", models.PositiveIntegerField(blank=True, null=True)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "length_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scopes",
                        to="operations.durationunit",
                    ),
                ),
                (
                    "work_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="scopes",
                        to="operations.worktype",
                    ),
                ),
                (
                    "workplace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scopes",
                        to="operations.workplace",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="projectscope",
            constraint=models.UniqueConstraint(
                fields=("workplace", "work_type"),
                name="unique_scope_work_type_per_project",
            ),
        ),
        migrations.AddField(
            model_name="sitereport",
            name="scope",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reports",
                to="operations.projectscope",
            ),
        ),
        migrations.RunPython(add_units_and_scopes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="workplace",
            name="length_unit_slug",
        ),
    ]
