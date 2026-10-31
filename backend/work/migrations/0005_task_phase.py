import django.db.models.deletion
from django.db import migrations, models

DEFAULT_PHASES = ("Design", "Preconstruction", "Procurement", "Execution", "Post construction")
SLUGS = {
    "design": "Design",
    "preconstruction": "Preconstruction",
    "procurement": "Procurement",
    "execution": "Execution",
    "post_construction": "Post construction",
}


def add_phases(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    Task = apps.get_model("work", "Task")
    TaskPhase = apps.get_model("work", "TaskPhase")
    for company in Company.objects.all():
        by_name = {}
        for position, name in enumerate(DEFAULT_PHASES):
            by_name[name] = TaskPhase.objects.create(company=company, name=name, position=position)
        execution = by_name["Execution"]
        for task in Task.objects.filter(company=company):
            task.phase_ref = by_name.get(SLUGS.get(task.phase, ""), execution)
            task.save(update_fields=["phase_ref"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("work", "0004_task_work_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskPhase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_phases",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="taskphase",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_task_phase_name"),
        ),
        migrations.AddField(
            model_name="task",
            name="phase_ref",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tasks",
                to="work.taskphase",
            ),
        ),
        migrations.RunPython(add_phases, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="task",
            name="phase",
        ),
        migrations.RenameField(
            model_name="task",
            old_name="phase_ref",
            new_name="phase",
        ),
        migrations.AlterField(
            model_name="task",
            name="phase",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tasks",
                to="work.taskphase",
            ),
        ),
    ]
