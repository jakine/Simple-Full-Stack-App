from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0012_duration_unit_and_scope"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="sitereport",
            constraint=models.UniqueConstraint(
                fields=("workplace", "team", "work_date", "scope"),
                name="unique_report_team_date_scope",
                nulls_distinct=False,
            ),
        ),
    ]
