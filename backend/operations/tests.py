from decimal import Decimal

from django.test import TestCase

from companies.models import Membership
from companies.testing import auth_client, make_membership, make_user
from inventory.models import Location
from operations.models import DurationUnit, ProjectScope, SiteReport, WorkKind, WorkMeasure, WorkType, WorkTypeCategory
from operations.services import create_default_duration_units, create_default_measures, default_duration_unit, default_work_category
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
        month = default_duration_unit(self.membership.company, "month")
        day = default_duration_unit(self.membership.company, "day")
        first = self.client.post(
            "/api/workplaces/",
            {"name": "Bridge", "status": "active", "length_count": 3, "length_unit": month.id},
            format="json",
        ).data
        second = self.client.post(
            "/api/workplaces/",
            {"name": "Yard wall", "status": "active", "length_count": 10, "length_unit": day.id},
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
        create_default_measures(self.membership.company)
        day = default_duration_unit(self.membership.company, "day")
        measure = WorkMeasure.objects.get(company=self.membership.company, symbol="m²")
        work_type = WorkType.objects.create(
            company=self.membership.company,
            name="Facade",
            measure=measure,
            category=default_work_category(self.membership.company),
        )
        contract = self.client.post(
            "/api/workplaces/",
            {
                "name": "Block B",
                "status": "active",
                "length_count": 20,
                "length_unit": day.id,
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
        self.assertEqual(detail.data["length_days"], "20.00")
        self.assertEqual(detail.data["remaining_days"], "18.00")
        self.assertEqual({row["team_name"] for row in detail.data["teams"]}, {"Team 1", "Team 2"})
        self.assertEqual(len(detail.data["scopes"]), 1)
        self.assertEqual(detail.data["scopes"][0]["remaining_quantity"], "35.00")

    def test_new_company_gets_default_measures(self):
        user = make_user("fresh-ops@example.com")
        client = auth_client(user, make_membership(user, "Temp Co").company)
        created = client.post("/api/companies/", {"name": "Measure Co"}, format="json")
        self.assertEqual(created.status_code, 201)
        measures = client.get("/api/work-measures/")
        self.assertEqual(measures.status_code, 200)
        self.assertEqual(
            {row["symbol"] for row in measures.data["results"]},
            {"m²", "m³", "m", "pcs", "t", "days"},
        )
        kinds = client.get("/api/work-kinds/")
        self.assertEqual([row["name"] for row in kinds.data], ["Area", "Volume", "Length", "Count", "Weight", "Time"])
        categories = client.get("/api/work-type-categories/")
        self.assertEqual(
            [row["name"] for row in categories.data],
            ["General", "Site", "Structure", "Envelope", "Finishes", "MEP"],
        )
        units = client.get("/api/duration-units/")
        self.assertEqual([row["name"] for row in units.data], ["Day", "Week", "Month"])
        self.assertEqual(units.data[2]["days_per_unit"], "30.00")

    def test_kinds_can_be_added_and_used_on_a_measure(self):
        create_default_measures(self.membership.company)
        created = self.client.post("/api/work-kinds/", {"name": "Percent"}, format="json")
        self.assertEqual(created.status_code, 201)
        measure = self.client.post(
            "/api/work-measures/",
            {"name": "Completion", "symbol": "%", "kind": created.data["id"]},
            format="json",
        )
        self.assertEqual(measure.status_code, 201)
        self.assertEqual(measure.data["kind_name"], "Percent")
        blocked = self.client.delete(f"/api/work-kinds/{created.data['id']}/")
        self.assertEqual(blocked.status_code, 400)
        ids = list(WorkKind.objects.filter(company=self.membership.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/work-kinds/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)

    def test_work_type_categories_can_be_added_and_used_on_a_type(self):
        create_default_measures(self.membership.company)
        category = default_work_category(self.membership.company)
        created = self.client.post("/api/work-type-categories/", {"name": "Civil"}, format="json")
        self.assertEqual(created.status_code, 201)
        measure = WorkMeasure.objects.get(company=self.membership.company, symbol="m³")
        work_type = self.client.post(
            "/api/work-types/",
            {"name": "Piling", "category": created.data["id"], "measure": measure.id},
            format="json",
        )
        self.assertEqual(work_type.status_code, 201)
        self.assertEqual(work_type.data["category_name"], "Civil")
        blocked = self.client.delete(f"/api/work-type-categories/{created.data['id']}/")
        self.assertEqual(blocked.status_code, 400)
        ids = list(WorkTypeCategory.objects.filter(company=self.membership.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/work-type-categories/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)
        unused = self.client.delete(f"/api/work-type-categories/{category.id}/")
        self.assertEqual(unused.status_code, 204)

    def test_task_work_type_sets_the_report_measure(self):
        create_default_measures(self.membership.company)
        square = WorkMeasure.objects.get(company=self.membership.company, symbol="m²")
        cube = WorkMeasure.objects.get(company=self.membership.company, symbol="m³")
        category = default_work_category(self.membership.company)
        facade = WorkType.objects.create(
            company=self.membership.company, name="Facade", measure=square, category=category
        )
        dig = WorkType.objects.create(
            company=self.membership.company, name="Excavation", measure=cube, category=category
        )
        team = Team.objects.create(company=self.membership.company, number=3, name="Team 3", worker_count=2)
        project = self.client.post(
            "/api/projects/",
            {"name": "Mixed site", "status": "active", "work_type": facade.id, "planned_quantity": "10.00"},
            format="json",
        ).data
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": project["id"], "team": team.id, "start_date": "2026-06-01"},
            format="json",
        )
        task = self.client.post(
            "/api/tasks/",
            {
                "title": "Dig pit",
                "project": project["id"],
                "team": team.id,
                "work_type": dig.id,
                "planned_quantity": "20.00",
            },
            format="json",
        ).data
        self.assertEqual(task["measure_symbol"], "m³")
        report = self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "task": task["id"],
                "work_date": "2026-06-08",
                "days": "1.00",
                "quantity": "4.00",
            },
            format="json",
        )
        self.assertEqual(report.status_code, 201, report.data)
        self.assertEqual(report.data["measure_symbol"], "m³")

    def test_duration_units_convert_project_length_to_days(self):
        create_default_duration_units(self.membership.company)
        created = self.client.post(
            "/api/duration-units/",
            {"name": "Fortnight", "symbol": "fn", "days_per_unit": "14.00", "timeline_step": "week"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        project = self.client.post(
            "/api/workplaces/",
            {"name": "Long job", "status": "active", "length_count": 2, "length_unit": created.data["id"]},
            format="json",
        )
        self.assertEqual(project.status_code, 201)
        self.assertEqual(project.data["length_days"], "28.00")
        blocked = self.client.delete(f"/api/duration-units/{created.data['id']}/")
        self.assertEqual(blocked.status_code, 400)
        unused = DurationUnit.objects.get(company=self.membership.company, symbol="week")
        removed = self.client.delete(f"/api/duration-units/{unused.id}/")
        self.assertEqual(removed.status_code, 204)
        ids = list(DurationUnit.objects.filter(company=self.membership.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/duration-units/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)

    def test_scopes_keep_mixed_units_separate(self):
        create_default_measures(self.membership.company)
        category = default_work_category(self.membership.company)
        square = WorkMeasure.objects.get(company=self.membership.company, symbol="m²")
        cube = WorkMeasure.objects.get(company=self.membership.company, symbol="m³")
        facade = WorkType.objects.create(
            company=self.membership.company, name="Facade", measure=square, category=category
        )
        dig = WorkType.objects.create(
            company=self.membership.company, name="Excavation", measure=cube, category=category
        )
        team = Team.objects.create(company=self.membership.company, number=4, name="Team 4", worker_count=2)
        project = self.client.post(
            "/api/projects/",
            {"name": "Mixed scopes", "status": "active", "work_type": facade.id, "planned_quantity": "100.00"},
            format="json",
        ).data
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": project["id"], "team": team.id, "start_date": "2026-06-01"},
            format="json",
        )
        second = self.client.post(
            "/api/project-scopes/",
            {"workplace": project["id"], "work_type": dig.id, "planned_quantity": "20.00", "teams_needed": 2},
            format="json",
        )
        self.assertEqual(second.status_code, 201, second.data)
        facade_scope = ProjectScope.objects.get(workplace_id=project["id"], work_type=facade)
        self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "scope": facade_scope.id,
                "work_date": "2026-06-09",
                "days": "1.00",
                "quantity": "40.00",
            },
            format="json",
        )
        self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "scope": second.data["id"],
                "work_date": "2026-06-10",
                "days": "1.00",
                "quantity": "5.00",
            },
            format="json",
        )
        detail = self.client.get(f"/api/projects/{project['id']}/")
        self.assertIsNone(detail.data["remaining_quantity"])
        self.assertIsNone(detail.data["progress_percent"])
        by_type = {row["work_type_name"]: row for row in detail.data["scopes"]}
        self.assertEqual(by_type["Facade"]["remaining_quantity"], "60.00")
        self.assertEqual(by_type["Excavation"]["remaining_quantity"], "15.00")
        self.assertEqual(detail.data["teams_needed"], 2)
        blocked = self.client.delete(f"/api/project-scopes/{facade_scope.id}/")
        self.assertEqual(blocked.status_code, 204)

    def _sheet_setup(self):
        create_default_measures(self.membership.company)
        category = default_work_category(self.membership.company)
        square = WorkMeasure.objects.get(company=self.membership.company, symbol="m²")
        cube = WorkMeasure.objects.get(company=self.membership.company, symbol="m³")
        facade = WorkType.objects.create(
            company=self.membership.company, name="Facade", measure=square, category=category
        )
        slab = WorkType.objects.create(
            company=self.membership.company, name="Slab", measure=cube, category=category
        )
        team = Team.objects.create(
            company=self.membership.company, number=5, name="Mira", worker_count=4, lead_note="Mira"
        )
        other = Team.objects.create(
            company=self.membership.company, number=6, name="Structure", worker_count=5, lead_note=""
        )
        project = self.client.post(
            "/api/projects/",
            {"name": "Sheet site", "status": "active", "work_type": facade.id, "planned_quantity": "100.00"},
            format="json",
        ).data
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": project["id"], "team": team.id, "start_date": "2026-06-01"},
            format="json",
        )
        self.client.post(
            "/api/workplace-teams/",
            {"workplace": project["id"], "team": other.id, "start_date": "2026-06-01"},
            format="json",
        )
        slab_scope = self.client.post(
            "/api/project-scopes/",
            {"workplace": project["id"], "work_type": slab.id, "planned_quantity": "80.00"},
            format="json",
        ).data
        facade_scope = ProjectScope.objects.get(workplace_id=project["id"], work_type=facade)
        return project, team, other, facade_scope, slab_scope

    def _add_column(self, workplace_id, kind, **fields):
        created = self.client.post(
            "/api/sheet-columns/",
            {"workplace": workplace_id, "kind": kind, **fields},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        return created.data

    def test_same_team_can_report_two_scopes_on_one_day(self):
        project, team, _other, facade_scope, slab_scope = self._sheet_setup()
        first = self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "scope": facade_scope.id,
                "work_date": "2026-06-11",
                "days": "1.00",
                "quantity": "12.00",
            },
            format="json",
        )
        second = self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "scope": slab_scope["id"],
                "work_date": "2026-06-11",
                "days": "1.00",
                "quantity": "6.00",
            },
            format="json",
        )
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        duplicate = self.client.post(
            "/api/site-reports/",
            {
                "workplace": project["id"],
                "team": team.id,
                "scope": facade_scope.id,
                "work_date": "2026-06-11",
                "days": "1.00",
                "quantity": "1.00",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        detail = self.client.get(f"/api/projects/{project['id']}/")
        by_type = {row["work_type_name"]: row for row in detail.data["scopes"]}
        self.assertEqual(by_type["Facade"]["remaining_quantity"], "88.00")
        self.assertEqual(by_type["Slab"]["remaining_quantity"], "74.00")
        self.assertIsNone(detail.data["remaining_quantity"])

    def test_sheet_upsert_updates_quantity_and_clears_the_cell(self):
        project, team, _other, facade_scope, _slab = self._sheet_setup()
        column = self._add_column(project["id"], "work_type", scope=facade_scope.id)
        created = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": column["id"],
                "team": team.id,
                "work_date": "2026-06-12",
                "quantity": "10.00",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 200, created.data)
        self.assertEqual(created.data["quantity"], "10.00")
        self.assertEqual(created.data["days"], "1.00")
        self.assertEqual(created.data["scope"], facade_scope.id)
        updated = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": column["id"],
                "team": team.id,
                "work_date": "2026-06-12",
                "quantity": "18.00",
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["id"], created.data["id"])
        self.assertEqual(updated.data["quantity"], "18.00")
        cleared = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": column["id"],
                "team": team.id,
                "work_date": "2026-06-12",
                "quantity": None,
            },
            format="json",
        )
        self.assertEqual(cleared.status_code, 200, cleared.data)
        self.assertTrue(cleared.data["deleted"])
        self.assertFalse(
            SiteReport.objects.filter(
                workplace_id=project["id"],
                team=team,
                work_date="2026-06-12",
                scope=facade_scope,
            ).exists()
        )

    def test_sheet_lead_cannot_write_another_team(self):
        project, team, other, facade_scope, _slab = self._sheet_setup()
        column = self._add_column(project["id"], "work_type", scope=facade_scope.id)
        other_column = self._add_column(project["id"], "team", team=other.id)
        lead = make_user("sheet-lead@example.com")
        Membership.objects.create(user=lead, company=self.membership.company, role=Membership.Role.TEAM_LEAD)
        team.lead_user = lead
        team.save(update_fields=["lead_user"])
        lead_client = auth_client(lead, self.membership.company)
        own = lead_client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": column["id"],
                "team": team.id,
                "work_date": "2026-06-13",
                "quantity": "4.00",
            },
            format="json",
        )
        self.assertEqual(own.status_code, 200, own.data)
        other_cell = lead_client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": column["id"],
                "team": other.id,
                "work_date": "2026-06-13",
                "quantity": "4.00",
            },
            format="json",
        )
        self.assertEqual(other_cell.status_code, 400)
        other_team_col = lead_client.post(
            f"/api/projects/{project['id']}/sheet/",
            {
                "column": other_column["id"],
                "scope": facade_scope.id,
                "work_date": "2026-06-13",
                "quantity": "4.00",
            },
            format="json",
        )
        self.assertEqual(other_team_col.status_code, 400)
        setup = lead_client.post(
            "/api/sheet-columns/",
            {"workplace": project["id"], "kind": "text", "name": "Notes"},
            format="json",
        )
        self.assertEqual(setup.status_code, 403)

    def test_sheet_is_filled_from_the_columns_that_were_set_up(self):
        project, team, other, facade_scope, slab_scope = self._sheet_setup()
        facade_col = self._add_column(project["id"], "work_type", scope=facade_scope.id)
        slab_col = self._add_column(project["id"], "work_type", scope=slab_scope["id"])
        team_col = self._add_column(project["id"], "team", team=other.id)
        note_col = self._add_column(project["id"], "text", name="Weather")
        facade = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {"column": facade_col["id"], "team": team.id, "work_date": "2026-06-14", "quantity": "8.00"},
            format="json",
        )
        slab = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {"column": slab_col["id"], "team": team.id, "work_date": "2026-06-14", "quantity": "5.00"},
            format="json",
        )
        crew = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {"column": team_col["id"], "scope": facade_scope.id, "work_date": "2026-06-14", "quantity": "2.00"},
            format="json",
        )
        note = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {"column": note_col["id"], "work_date": "2026-06-14", "text": "Rain after lunch"},
            format="json",
        )
        self.assertEqual(facade.status_code, 200, facade.data)
        self.assertEqual(slab.status_code, 200, slab.data)
        self.assertEqual(crew.status_code, 200, crew.data)
        self.assertEqual(note.status_code, 200, note.data)
        self.assertEqual(note.data["text"], "Rain after lunch")
        cleared = self.client.post(
            f"/api/projects/{project['id']}/sheet/",
            {"column": note_col["id"], "work_date": "2026-06-14", "text": ""},
            format="json",
        )
        self.assertEqual(cleared.status_code, 200, cleared.data)
        self.assertTrue(cleared.data["deleted"])
        detail = self.client.get(f"/api/projects/{project['id']}/")
        self.assertEqual([row["kind"] for row in detail.data["sheet_columns"]], ["work_type", "work_type", "team", "text"])
        self.assertEqual(detail.data["sheet_texts"], [])
        ids = [row["id"] for row in reversed(detail.data["sheet_columns"])]
        reordered = self.client.post(
            "/api/sheet-columns/reorder/",
            {"workplace": project["id"], "ids": ids},
            format="json",
        )
        self.assertEqual(reordered.status_code, 200, reordered.data)
        self.assertEqual([row["id"] for row in reordered.data], ids)
