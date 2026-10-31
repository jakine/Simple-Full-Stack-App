from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from companies.models import Membership
from companies.testing import auth_client, make_membership, make_user
from workforce.models import Team

User = get_user_model()


class CompanyTenancyTests(TestCase):
    def test_register_creates_an_account_and_signs_in(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register/",
            {"email": "new-owner@example.com", "password": "Manager-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "new-owner@example.com")
        self.assertIsNone(response.data["active_company"])

        company = client.post("/api/companies/", {"name": "Fresh Co"}, format="json")
        self.assertEqual(company.status_code, 201)
        self.assertEqual(company.data["role"], "owner")
    def test_create_company_makes_owner_and_selects_it(self):
        user = make_user("owner@example.com")
        client = APIClient()
        client.force_login(user)

        response = client.post("/api/companies/", {"name": "North Build"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], Membership.Role.OWNER)
        self.assertEqual(client.session["company_id"], response.data["id"])

    def test_login_selects_the_only_company(self):
        user = make_user("solo@example.com")
        membership = make_membership(user, "Solo Co")
        client = APIClient()

        response = client.post(
            "/api/auth/login/",
            {"email": "solo@example.com", "password": "Manager-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_company"]["id"], membership.company_id)

    def test_login_with_two_companies_waits_for_a_switch(self):
        user = make_user("multi@example.com")
        make_membership(user, "One")
        make_membership(user, "Two")
        client = APIClient()

        response = client.post(
            "/api/auth/login/",
            {"email": "multi@example.com", "password": "Manager-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["active_company"])
        self.assertEqual(len(response.data["companies"]), 2)

    def test_switch_rejects_a_company_the_user_does_not_belong_to(self):
        user = make_user("a@example.com")
        other = make_user("b@example.com")
        membership = make_membership(user, "A")
        outsider = make_membership(other, "B")
        client = auth_client(user, membership.company)

        response = client.post(
            "/api/companies/switch/",
            {"company_id": outsider.company_id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(client.session["company_id"], membership.company_id)

    def test_only_owner_can_invite_a_manager(self):
        owner = make_user("owner2@example.com")
        manager = make_user("manager@example.com")
        membership = make_membership(owner, "Crew Co")
        Membership.objects.create(
            user=manager,
            company=membership.company,
            role=Membership.Role.MANAGER,
        )
        manager_client = auth_client(manager, membership.company)
        denied = manager_client.post(
            "/api/companies/members/",
            {"email": "new@example.com", "password": "Manager-pass-123"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        owner_client = auth_client(owner, membership.company)
        created = owner_client.post(
            "/api/companies/members/",
            {"email": "new@example.com", "password": "Manager-pass-123"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["role"], Membership.Role.MANAGER)
        self.assertTrue(User.objects.filter(username="new@example.com").exists())

    def test_invite_of_existing_member_conflicts(self):
        owner = make_user("owner3@example.com")
        membership = make_membership(owner, "Again Co")
        client = auth_client(owner, membership.company)

        response = client.post(
            "/api/companies/members/",
            {"email": "owner3@example.com", "password": "Manager-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_owner_can_invite_a_team_lead_and_link_a_team(self):
        owner = make_user("boss@example.com")
        membership = make_membership(owner, "Crew Co")
        client = auth_client(owner, membership.company)
        team = Team.objects.create(
            company=membership.company, number=1, name="Team 1", worker_count=2, lead_note="Mira"
        )
        created = client.post(
            "/api/companies/members/",
            {
                "email": "lead@example.com",
                "password": "Manager-pass-123",
                "role": "team_lead",
                "team": team.id,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["role"], Membership.Role.TEAM_LEAD)
        team.refresh_from_db()
        self.assertEqual(team.lead_user.email, "lead@example.com")
