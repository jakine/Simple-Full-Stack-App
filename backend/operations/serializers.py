from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers

from operations.models import SiteReport, WorkMeasure, Workplace, WorkplaceTeam, WorkType
from operations.services import prepare_site_report
from workforce.services import ranges_overlap


class WorkplaceSerializer(serializers.ModelSerializer):
    work_type_name = serializers.CharField(source="work_type.name", read_only=True, allow_null=True)
    measure_symbol = serializers.CharField(source="work_type.measure.symbol", read_only=True, allow_null=True)
    done_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_worked = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    progress_percent = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Workplace
        fields = [
            "id",
            "name",
            "address",
            "status",
            "start_date",
            "end_date",
            "length_count",
            "length_unit",
            "work_type",
            "work_type_name",
            "measure_symbol",
            "planned_quantity",
            "done_quantity",
            "days_worked",
            "remaining_quantity",
            "progress_percent",
        ]

    def validate_work_type(self, work_type):
        if work_type is None:
            return work_type
        if work_type.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Work type must belong to this company.")
        return work_type

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        length_count = attrs.get("length_count", getattr(self.instance, "length_count", None))
        length_unit = attrs.get("length_unit", getattr(self.instance, "length_unit", ""))
        if bool(length_count) != bool(length_unit):
            raise serializers.ValidationError(
                {"length_unit": "Set both the contract length and whether it is days, weeks, or months."}
            )
        planned = attrs.get("planned_quantity", getattr(self.instance, "planned_quantity", None))
        if planned is not None and planned <= 0:
            raise serializers.ValidationError({"planned_quantity": "Planned amount must be greater than zero."})
        return attrs

    def to_representation(self, instance):
        done = getattr(instance, "done_quantity", None)
        days = getattr(instance, "days_worked", None)
        if done is None or days is None:
            totals = instance.reports.aggregate(
                done=Coalesce(Sum("quantity"), Decimal("0.00")),
                days=Coalesce(Sum("days"), Decimal("0.00")),
            )
            done = totals["done"]
            days = totals["days"]
        instance.done_quantity = done or Decimal("0.00")
        instance.days_worked = days or Decimal("0.00")
        if instance.planned_quantity:
            instance.remaining_quantity = instance.planned_quantity - instance.done_quantity
            instance.progress_percent = (
                instance.done_quantity / instance.planned_quantity * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            instance.remaining_quantity = None
            instance.progress_percent = None
        return super().to_representation(instance)


class WorkplaceTeamSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    team_number = serializers.IntegerField(source="team.number", read_only=True)
    worker_count = serializers.IntegerField(source="team.worker_count", read_only=True)
    lead_note = serializers.CharField(source="team.lead_note", read_only=True)
    lead_user_email = serializers.SerializerMethodField()
    workplace_name = serializers.CharField(source="workplace.name", read_only=True)

    class Meta:
        model = WorkplaceTeam
        fields = [
            "id",
            "workplace",
            "workplace_name",
            "team",
            "team_name",
            "team_number",
            "worker_count",
            "lead_note",
            "lead_user_email",
            "start_date",
            "end_date",
        ]

    def get_lead_user_email(self, obj):
        if obj.team.lead_user_id is None:
            return ""
        return obj.team.lead_user.email

    def validate(self, attrs):
        workplace = attrs.get("workplace") or self.instance.workplace
        team = attrs.get("team") or self.instance.team
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        company = self.context["request"].company
        if workplace.company_id != company.id:
            raise serializers.ValidationError({"workplace": "Contract must belong to this company."})
        if team.company_id != company.id:
            raise serializers.ValidationError({"team": "Team must belong to this company."})
        if end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        existing = WorkplaceTeam.objects.filter(workplace=workplace, team=team)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        for row in existing:
            if ranges_overlap(row.start_date, row.end_date, start_date, end_date):
                raise serializers.ValidationError("This team is already on that contract for those dates.")
        return attrs


class WorkMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkMeasure
        fields = ["id", "name", "symbol"]


class WorkTypeSerializer(serializers.ModelSerializer):
    measure_name = serializers.CharField(source="measure.name", read_only=True)
    measure_symbol = serializers.CharField(source="measure.symbol", read_only=True)

    class Meta:
        model = WorkType
        fields = ["id", "name", "measure", "measure_name", "measure_symbol"]

    def validate_measure(self, measure):
        if measure.company_id != self.context["request"].company.id:
            raise serializers.ValidationError("Measure must belong to this company.")
        return measure


class SiteReportSerializer(serializers.ModelSerializer):
    workplace_name = serializers.CharField(source="workplace.name", read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True, allow_null=True)
    team_number = serializers.IntegerField(source="team.number", read_only=True, allow_null=True)
    measure_symbol = serializers.CharField(source="workplace.work_type.measure.symbol", read_only=True, allow_null=True)

    class Meta:
        model = SiteReport
        fields = [
            "id",
            "workplace",
            "workplace_name",
            "team",
            "team_number",
            "team_name",
            "work_date",
            "days",
            "quantity",
            "measure_symbol",
            "note",
        ]

    def validate(self, attrs):
        workplace = attrs.get("workplace") or getattr(self.instance, "workplace", None)
        company = self.context["request"].company
        if workplace.company_id != company.id:
            raise serializers.ValidationError({"workplace": "Contract must belong to this company."})
        team = attrs["team"] if "team" in attrs else getattr(self.instance, "team", None)
        if team is not None and team.company_id != company.id:
            raise serializers.ValidationError({"team": "Team must belong to this company."})
        return prepare_site_report(attrs, instance=self.instance)
