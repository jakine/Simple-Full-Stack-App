from django.db import migrations

DEFAULT_STATUSES = (
    ("To do", "todo"),
    ("In progress", "in_progress"),
    ("Inspection", "in_progress"),
    ("Done", "done"),
)


def add_default_statuses(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    TaskStatus = apps.get_model("work", "TaskStatus")
    for company in Company.objects.all():
        if TaskStatus.objects.filter(company=company).exists():
            continue
        TaskStatus.objects.bulk_create(
            TaskStatus(company=company, name=name, category=category, position=position)
            for position, (name, category) in enumerate(DEFAULT_STATUSES)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0002_team_lead_role"),
        ("work", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_default_statuses, migrations.RunPython.noop),
    ]
