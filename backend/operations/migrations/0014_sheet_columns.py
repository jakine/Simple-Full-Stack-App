import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0013_report_team_date_scope"),
        ("workforce", "0005_simpler_contracts"),
    ]

    operations = [
        migrations.CreateModel(
            name="SheetColumn",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("work_type", "Work type"), ("team", "Team"), ("text", "Text")], max_length=20)),
                ("name", models.CharField(blank=True, max_length=120)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "scope",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sheet_columns",
                        to="operations.projectscope",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sheet_columns",
                        to="workforce.team",
                    ),
                ),
                (
                    "workplace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sheet_columns",
                        to="operations.workplace",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.CreateModel(
            name="SheetTextCell",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("work_date", models.DateField()),
                ("text", models.CharField(blank=True, max_length=300)),
                (
                    "column",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="text_cells",
                        to="operations.sheetcolumn",
                    ),
                ),
            ],
            options={
                "ordering": ["work_date", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="sheettextcell",
            constraint=models.UniqueConstraint(fields=("column", "work_date"), name="unique_sheet_text_cell"),
        ),
    ]
