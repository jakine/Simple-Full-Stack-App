import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_team_crews(apps, schema_editor):
    Team = apps.get_model("workforce", "Team")
    Worker = apps.get_model("workforce", "Worker")
    next_number = {}
    for team in Team.objects.order_by("company_id", "id"):
        next_number[team.company_id] = next_number.get(team.company_id, 0) + 1
        leaders = Worker.objects.filter(team_id=team.id, team_role="leader").order_by("name")
        team.number = next_number[team.company_id]
        team.worker_count = Worker.objects.filter(team_id=team.id).count()
        team.lead_note = ", ".join(leader.name for leader in leaders)
        team.save(update_fields=["number", "worker_count", "lead_note"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("workforce", "0003_worker_types_and_team_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="number",
            field=models.PositiveIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="team",
            name="worker_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="team",
            name="lead_note",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="team",
            name="lead_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="led_teams",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(fill_team_crews, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="team",
            name="number",
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterModelOptions(
            name="team",
            options={"ordering": ["number", "name"]},
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(fields=("company", "number"), name="unique_team_number"),
        ),
    ]
