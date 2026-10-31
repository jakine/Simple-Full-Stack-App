from django.test import TestCase
from rest_framework.test import APIClient

from companies.testing import auth_client, make_membership, make_user
from workforce.models import Worker


class WorkforceApiTests(TestCase):
    def setUp(self):
        self.user = make_user("lead@example.com")
        self.membership = make_membership(self.user, "North")
        self.client = auth_client(self.user, self.membership.company)
        self.other_user = make_user("other@example.com")
        self.other = make_membership(self.other_user, "South")

    def test_workers_are_scoped_to_the_active_company(self):
        Worker.objects.create(company=self.membership.company, name="Ada")
        Worker.objects.create(company=self.other.company, name="Hidden")

        response = self.client.get("/api/workers/")

        self.assertEqual(response.status_code, 200)
        names = [row["name"] for row in response.data["results"]]
        self.assertEqual(names, ["Ada"])

    def test_a_worker_belongs_to_a_team(self):
        created = self.client.post(
            "/api/teams/",
            {"number": 1, "name": "Team 1", "worker_count": 4, "lead_note": "Mira"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        worker = self.client.post(
            "/api/workers/",
            {"name": "Ada", "team": created.data["id"]},
            format="json",
        )
        self.assertEqual(worker.status_code, 201)
        self.assertEqual(worker.data["team_name"], "Team 1")
        self.assertEqual(worker.data["team_number"], 1)

    def test_requests_without_a_company_are_rejected(self):
        client = APIClient()
        client.force_login(self.user)
        response = client.get("/api/workers/")
        self.assertEqual(response.status_code, 403)
