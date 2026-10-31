import django.db.models.deletion
from django.db import migrations, models

OLD_TO_NAME = {
    "area": "Area",
    "volume": "Volume",
    "length": "Length",
    "count": "Count",
    "weight": "Weight",
    "time": "Time",
}

DEFAULT_KINDS = ("Area", "Volume", "Length", "Count", "Weight", "Time")


def migrate_kinds(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    WorkKind = apps.get_model("operations", "WorkKind")
    WorkMeasure = apps.get_model("operations", "WorkMeasure")
    for company in Company.objects.all():
        kinds = {}
        for position, name in enumerate(DEFAULT_KINDS):
            kinds[name] = WorkKind.objects.create(company=company, name=name, position=position)
        extra = len(DEFAULT_KINDS)
        for measure in WorkMeasure.objects.filter(company=company):
            name = OLD_TO_NAME.get(measure.kind, (measure.kind or "Area").replace("_", " ").title())
            kind = kinds.get(name)
            if kind is None:
                kind = WorkKind.objects.create(company=company, name=name, position=extra)
                kinds[name] = kind
                extra += 1
            measure.kind_new = kind
            measure.save(update_fields=["kind_new"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("operations", "0009_measure_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkKind",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_kinds",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="workkind",
            constraint=models.UniqueConstraint(fields=("company", "name"), name="unique_work_kind_name"),
        ),
        migrations.AddField(
            model_name="workmeasure",
            name="kind_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="measures",
                to="operations.workkind",
            ),
        ),
        migrations.RunPython(migrate_kinds, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="workmeasure",
            name="kind",
        ),
        migrations.RenameField(
            model_name="workmeasure",
            old_name="kind_new",
            new_name="kind",
        ),
        migrations.AlterField(
            model_name="workmeasure",
            name="kind",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="measures",
                to="operations.workkind",
            ),
        ),
    ]
