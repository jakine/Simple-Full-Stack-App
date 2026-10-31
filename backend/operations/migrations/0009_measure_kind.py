from django.db import migrations, models

DEFAULT_MEASURES = (
    ("Square meters", "m²", "area"),
    ("Cubic meters", "m³", "volume"),
    ("Linear meters", "m", "length"),
    ("Pieces", "pcs", "count"),
    ("Tonnes", "t", "weight"),
    ("Days", "days", "time"),
)


def infer_kind(symbol):
    text = (symbol or "").lower().replace("²", "2").replace("³", "3")
    if "m2" in text or "sq" in text:
        return "area"
    if "m3" in text or "cu" in text:
        return "volume"
    if text in {"m", "lm", "ml"} or "linear" in text:
        return "length"
    if text in {"pcs", "pc", "nr", "no"} or "piece" in text:
        return "count"
    if text in {"t", "kg", "ton", "tonne"}:
        return "weight"
    if "day" in text:
        return "time"
    return "area"


def add_kinds_and_defaults(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    WorkMeasure = apps.get_model("operations", "WorkMeasure")
    for measure in WorkMeasure.objects.all():
        measure.kind = infer_kind(measure.symbol)
        measure.save(update_fields=["kind"])
    for company in Company.objects.all():
        for name, symbol, kind in DEFAULT_MEASURES:
            WorkMeasure.objects.get_or_create(
                company=company,
                name=name,
                defaults={"symbol": symbol, "kind": kind},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0008_sitereport_task"),
    ]

    operations = [
        migrations.AddField(
            model_name="workmeasure",
            name="kind",
            field=models.CharField(
                choices=[
                    ("area", "Area"),
                    ("volume", "Volume"),
                    ("length", "Length"),
                    ("count", "Count"),
                    ("weight", "Weight"),
                    ("time", "Time"),
                ],
                default="area",
                max_length=20,
            ),
        ),
        migrations.RunPython(add_kinds_and_defaults, migrations.RunPython.noop),
    ]
