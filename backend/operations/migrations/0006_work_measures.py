import django.db.models.deletion
from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def assign_unit_measures(apps, schema_editor):
    WorkMeasure = apps.get_model("operations", "WorkMeasure")
    WorkType = apps.get_model("operations", "WorkType")
    company_ids = WorkType.objects.values_list("company_id", flat=True).distinct()
    for company_id in company_ids:
        measure, _created = WorkMeasure.objects.get_or_create(
            company_id=company_id,
            name="Unit",
            defaults={"symbol": "unit"},
        )
        WorkType.objects.filter(company_id=company_id, measure_id=None).update(measure_id=measure.id)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("companies", "0001_initial"),
        ("operations", "0005_site_reports"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkMeasure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("symbol", models.CharField(max_length=20)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_measures",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="workmeasure",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_work_measure_name"),
        ),
        migrations.AddField(
            model_name="worktype",
            name="measure",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_types",
                to="operations.workmeasure",
            ),
        ),
        migrations.RunPython(assign_unit_measures, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="worktype",
            name="measure",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_types",
                to="operations.workmeasure",
            ),
        ),
        migrations.AddField(
            model_name="workitem",
            name="planned_quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
            ),
        ),
        migrations.AddField(
            model_name="sitereport",
            name="quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
            ),
        ),
    ]
