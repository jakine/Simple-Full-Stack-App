import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0009_measure_kind"),
        ("work", "0003_task_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="work_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="operations.worktype",
            ),
        ),
    ]
