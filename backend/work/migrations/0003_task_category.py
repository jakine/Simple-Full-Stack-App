import django.db.models.deletion
from django.db import migrations, models

OLD_TO_NAME = {
    "todo": "To do",
    "in_progress": "In progress",
    "done": "Done",
}

DEFAULT_CATEGORIES = (
    ("To do", "#8a9696"),
    ("In progress", "#01696f"),
    ("Done", "#2e7d32"),
)


def migrate_categories(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    TaskCategory = apps.get_model("work", "TaskCategory")
    TaskStatus = apps.get_model("work", "TaskStatus")
    for company in Company.objects.all():
        categories = {}
        for position, (name, color) in enumerate(DEFAULT_CATEGORIES):
            categories[name] = TaskCategory.objects.create(
                company=company, name=name, color=color, position=position
            )
        extra = len(DEFAULT_CATEGORIES)
        for status in TaskStatus.objects.filter(company=company):
            name = OLD_TO_NAME.get(status.category, status.category.replace("_", " ").title() or "To do")
            category = categories.get(name)
            if category is None:
                category = TaskCategory.objects.create(
                    company=company, name=name, color="#01696f", position=extra
                )
                categories[name] = category
                extra += 1
            status.category_new = category
            status.save(update_fields=["category_new"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("work", "0002_default_statuses"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("color", models.CharField(default="#01696f", max_length=7)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_categories",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="taskcategory",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_task_category_name"),
        ),
        migrations.AddField(
            model_name="taskstatus",
            name="category_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="statuses",
                to="work.taskcategory",
            ),
        ),
        migrations.RunPython(migrate_categories, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="taskstatus",
            name="category",
        ),
        migrations.RenameField(
            model_name="taskstatus",
            old_name="category_new",
            new_name="category",
        ),
        migrations.AlterField(
            model_name="taskstatus",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="statuses",
                to="work.taskcategory",
            ),
        ),
    ]
