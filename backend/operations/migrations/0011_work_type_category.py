import django.db.models.deletion
from django.db import migrations, models

DEFAULT_CATEGORIES = ("General", "Site", "Structure", "Envelope", "Finishes", "MEP")


def add_categories(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    WorkType = apps.get_model("operations", "WorkType")
    WorkTypeCategory = apps.get_model("operations", "WorkTypeCategory")
    for company in Company.objects.all():
        general = None
        for position, name in enumerate(DEFAULT_CATEGORIES):
            category = WorkTypeCategory.objects.create(company=company, name=name, position=position)
            if name == "General":
                general = category
        WorkType.objects.filter(company=company).update(category=general)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("operations", "0010_work_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkTypeCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_type_categories",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="worktypecategory",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_work_type_category_name"),
        ),
        migrations.AddField(
            model_name="worktype",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_types",
                to="operations.worktypecategory",
            ),
        ),
        migrations.RunPython(add_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="worktype",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="work_types",
                to="operations.worktypecategory",
            ),
        ),
    ]
