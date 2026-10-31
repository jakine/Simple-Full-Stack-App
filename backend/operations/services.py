from django.db import transaction
from rest_framework.exceptions import ValidationError

from inventory.models import Location
from operations.models import SiteReport, Workplace


def create_workplace(company, **fields):
    with transaction.atomic():
        workplace = Workplace.objects.create(company=company, **fields)
        Location.objects.create(
            company=company,
            name=workplace.name,
            kind=Location.Kind.SITE,
            workplace=workplace,
        )
    return workplace


def sync_workplace_location(workplace):
    Location.objects.filter(workplace=workplace).update(name=workplace.name)


def prepare_site_report(attrs, instance=None):
    workplace = attrs.get("workplace") or instance.workplace
    work_date = attrs.get("work_date", getattr(instance, "work_date", None))
    team = attrs["team"] if "team" in attrs else getattr(instance, "team", None)
    quantity = attrs["quantity"] if "quantity" in attrs else getattr(instance, "quantity", None)
    days = attrs.get("days", getattr(instance, "days", None))

    if quantity is None or quantity <= 0:
        raise ValidationError({"quantity": "Enter how much was done."})
    if days is None or days <= 0:
        raise ValidationError({"days": "Enter how many days were worked."})
    if not workplace.workplace_teams.exists():
        raise ValidationError({"team": "Place a team on this contract before filling a report."})
    if team is None:
        raise ValidationError({"team": "Choose the team that did this work."})
    if not workplace.workplace_teams.filter(team=team).exists():
        raise ValidationError({"team": "That team is not on this contract."})

    existing = SiteReport.objects.filter(workplace=workplace, team=team, work_date=work_date)
    if instance is not None:
        existing = existing.exclude(pk=instance.pk)
    if existing.exists():
        raise ValidationError("That team already has a report on this contract for that date.")
    return attrs
