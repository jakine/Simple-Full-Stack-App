from decimal import Decimal

from django.test import TestCase

from companies.testing import auth_client, make_membership, make_user
from inventory.models import Location
from operations.models import WorkMeasure, WorkType
from workforce.models import Team, Worker


class OperationsApiTests(TestCase):
    def setUp(self):
        self.user = make_user("ops@example.com")
        self.membership = make_membership(self.user, "Sites")
        self.client = auth_client(self.user, self.membership.company)
        self.worker = Worker.objects.create(company=self.membership.company, name="Ada")

    def test_workplace_creates_a_site_stock_location(self):
        response = self.client.post(
            "/api/workplaces/",
            {"name": "River bridge", "address": "12 Bank St", "status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        location = Location.objects.get(workplace_id=response.data["id"])
        self.assertEqual(location.kind, Location.Kind.SITE)
        self.assertEqual(location.name, "River bridge")

    def test_one_team_can_work_on_more_than_one_contract(self):
        team = Team.objects.create(
            company=self.membership.company,
            name="Team 1",
            number=1,
            worker_count=8,
            lead_note="Mira",
        )
        first = self.client.post(
            "/api/workplaces/",
            {"name": "Bridge", "status": "active", "length_count": 3, "length_unit": "month"},
            format="json",
        ).data
        second = self.client.post(
            "/api/workplaces/",
            {"name": "Yard wall", "status": "active", "length_count": 10, "length_unit": "day"},
            format="json",
        ).data
        for workplace_id in (first["id"], second["id"]):
            placed = self.client.post(
                "/api/workplace-teams/",
                {"workplace": workplace_id, "team": team.id, "start_date": "2026-05-01"},
                format="json",
            )
            self.assertEqual(placed.status_code, 201)

        contracts = self.client.get(f"/api/workplace-teams/?team={team.id}")
        self.assertEqual(contracts.status_code, 200)
        self.assertEqual(
            {row["workplace_name"] for row in contracts.data["results"]},
            {"Bridge", "Yard wall"},
        )

    def test_reports_track_days_and_measured_progress(self):
        team = Team.objects.create(
            company=self.membership.company,
            name="Team 1",
            number=1,
            worker_count=4,
            lead_note="Mira",
        )
        other = Team.objects.create(
            company=self.membership.company,
            name="Team 2",
            number=2,
            worker_count=3,
            lead_note="",
        )
        measure = WorkMeasure.objects.create(company=self.membership.company, name="Square meters", symbol="m²")
        work_type = WorkType.objects.create(company=self.membership.company, name="Facade", measure=measure)
        contract = self.client.post(
            "/api/workplaces/",
            {
                "name": "Block B",
                "status": "active",
                "length_count": 20,
                "length_unit": "day",
                "work_type": work_type.id,
                "planned_quantity": "100.00",
            },
            format="json",
        ).data
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": contract["id"], "team": team.id, "start_date": "2026-06-01"},
            format="json",
        )
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": contract["id"], "team": other.id, "start_date": "2026-06-01"},
            format="json",
        )
        for amount, day in (("40.00", "2026-06-02"), ("25.00", "2026-06-03")):
            created = self.client.post(
                "/api/site-reports/",
                {
                    "workplace": contract["id"],
                    "team": team.id,
                    "work_date": day,
                    "days": "1.00",
                    "quantity": amount,
                },
                format="json",
            )
            self.assertEqual(created.status_code, 201, created.data)

        detail = self.client.get(f"/api/workplaces/{contract['id']}/")
        self.assertEqual(detail.data["measure_symbol"], "m²")
        self.assertEqual(detail.data["done_quantity"], "65.00")
        self.assertEqual(detail.data["days_worked"], "2.00")
        self.assertEqual(detail.data["remaining_quantity"], "35.00")
        self.assertEqual(detail.data["progress_percent"], "65.00")
        self.assertEqual({row["team_name"] for row in detail.data["teams"]}, {"Team 1", "Team 2"})
