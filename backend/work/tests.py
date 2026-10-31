from decimal import Decimal

from django.test import TestCase

from companies.models import Membership
from companies.testing import auth_client, make_membership, make_user
from core.models import ActivityEvent
from core.services import target_label
from operations.models import SiteReport, WorkMeasure, WorkType, WorkplaceTeam
from operations.services import create_default_measures, create_workplace, default_work_category
from work.models import Task, TaskCategory, TaskPhase, TaskStatus
from work.services import create_default_phases, create_default_statuses, create_task
from workforce.models import Team


class WorkApiTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.membership = make_membership(self.owner, "Build Co")
        self.company = self.membership.company
        self.client = auth_client(self.owner, self.company)
        create_default_statuses(self.company)
        create_default_phases(self.company)
        self.todo = TaskStatus.objects.get(company=self.company, name="To do")
        self.doing = TaskStatus.objects.get(company=self.company, name="In progress")
        self.done = TaskStatus.objects.get(company=self.company, name="Done")
        self.team = Team.objects.create(
            company=self.company, number=1, name="Team 1", worker_count=4, lead_note="Mira"
        )
        self.other_team = Team.objects.create(
            company=self.company, number=2, name="Team 2", worker_count=3, lead_note=""
        )
        self.project = create_workplace(self.company, name="Bridge", status="active")
        self.other_project = create_workplace(self.company, name="Yard", status="planned")
        WorkplaceTeam.objects.create(workplace=self.project, team=self.team, start_date="2026-06-01")
        WorkplaceTeam.objects.create(workplace=self.project, team=self.other_team, start_date="2026-06-01")

    def _lead_client(self, team):
        lead = make_user("lead@example.com")
        Membership.objects.create(user=lead, company=self.company, role=Membership.Role.TEAM_LEAD)
        team.lead_user = lead
        team.save(update_fields=["lead_user"])
        return auth_client(lead, self.company), lead

    def test_create_company_adds_default_task_statuses(self):
        user = make_user("fresh@example.com")
        client = auth_client(user, make_membership(user, "Fresh Co").company)
        created = client.post("/api/companies/", {"name": "New Co"}, format="json")
        self.assertEqual(created.status_code, 201)
        statuses = client.get("/api/task-statuses/")
        self.assertEqual(statuses.status_code, 200)
        self.assertEqual([row["name"] for row in statuses.data], ["To do", "In progress", "Inspection", "Done"])
        categories = client.get("/api/task-categories/")
        self.assertEqual([row["name"] for row in categories.data], ["To do", "In progress", "Done"])
        measures = client.get("/api/work-measures/")
        self.assertIn("m²", {row["symbol"] for row in measures.data["results"]})
        kinds = client.get("/api/work-kinds/")
        self.assertIn("Area", {row["name"] for row in kinds.data})
        phases = client.get("/api/task-phases/")
        self.assertEqual(
            [row["name"] for row in phases.data],
            ["Design", "Preconstruction", "Procurement", "Execution", "Post construction"],
        )

    def test_tasks_are_scoped_to_the_active_company(self):
        create_task(self.company, self.project, self.owner, title="Hidden", status=self.todo)
        other_user = make_user("other@example.com")
        other = make_membership(other_user, "South")
        create_default_statuses(other.company)
        other_client = auth_client(other_user, other.company)
        listed = other_client.get("/api/tasks/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["results"], [])

    def test_projects_alias_lists_workplaces(self):
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["name"] for row in response.data["results"]}, {"Bridge", "Yard"})

    def test_task_move_changes_status_and_records_activity(self):
        created = self.client.post(
            "/api/tasks/",
            {"title": "Pour slab", "project": self.project.id, "team": self.team.id},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["key"], f"P{self.project.id}-1")
        self.assertEqual(created.data["status"], self.todo.id)
        self.assertEqual(created.data["phase_name"], "Execution")

        moved = self.client.post(
            f"/api/tasks/{created.data['id']}/move/",
            {"status": self.doing.id, "position": 0},
            format="json",
        )
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.data["status"], self.doing.id)

        activity = self.client.get(f"/api/tasks/{created.data['id']}/activity/")
        self.assertEqual(activity.status_code, 200)
        self.assertEqual({row["verb"] for row in activity.data}, {"task.created", "task.moved"})

    def test_task_activity_stays_in_the_company(self):
        created = self.client.post(
            "/api/tasks/",
            {"title": "Pour slab", "project": self.project.id},
            format="json",
        )
        task = Task.objects.get(pk=created.data["id"])
        other_user = make_user("south@example.com")
        other = make_membership(other_user, "South")
        ActivityEvent.objects.create(
            company=other.company,
            actor=other_user,
            verb="task.created",
            target_type=target_label(task),
            target_id=task.pk,
            data={"leaked": True},
        )
        activity = self.client.get(f"/api/tasks/{task.id}/activity/")
        self.assertEqual(activity.status_code, 200)
        self.assertFalse(any(row.get("data", {}).get("leaked") for row in activity.data))

    def test_task_progress_comes_from_linked_reports(self):
        create_default_measures(self.company)
        measure = WorkMeasure.objects.get(company=self.company, symbol="m²")
        work_type = WorkType.objects.create(
            company=self.company,
            name="Slab",
            measure=measure,
            category=default_work_category(self.company),
        )
        self.project.work_type = work_type
        self.project.save(update_fields=["work_type"])
        task = create_task(
            self.company,
            self.project,
            self.owner,
            title="North bay",
            team=self.team,
            planned_quantity=Decimal("100.00"),
            status=self.todo,
        )
        SiteReport.objects.create(
            workplace=self.project,
            team=self.team,
            task=task,
            work_date="2026-06-02",
            days=Decimal("1.00"),
            quantity=Decimal("40.00"),
        )
        SiteReport.objects.create(
            workplace=self.project,
            team=self.other_team,
            task=task,
            work_date="2026-06-03",
            days=Decimal("1.00"),
            quantity=Decimal("25.00"),
        )
        detail = self.client.get(f"/api/tasks/{task.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["done_quantity"], "65.00")
        self.assertEqual(detail.data["progress_percent"], "65.00")

    def test_team_must_be_on_the_project_and_due_date_cannot_precede_start(self):
        outsider = Team.objects.create(company=self.company, number=9, name="Away", worker_count=1)
        denied = self.client.post(
            "/api/tasks/",
            {"title": "Offsite", "project": self.project.id, "team": outsider.id},
            format="json",
        )
        self.assertEqual(denied.status_code, 400)

        dates = self.client.post(
            "/api/tasks/",
            {
                "title": "Late start",
                "project": self.project.id,
                "start_date": "2026-06-10",
                "due_date": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(dates.status_code, 400)

    def test_team_lead_sees_only_their_projects_and_cannot_set_up_work(self):
        lead_client, _lead = self._lead_client(self.team)
        projects = lead_client.get("/api/projects/")
        self.assertEqual(projects.status_code, 200)
        self.assertEqual([row["name"] for row in projects.data["results"]], ["Bridge"])

        hidden = lead_client.get(f"/api/projects/{self.other_project.id}/")
        self.assertEqual(hidden.status_code, 404)

        created = lead_client.post("/api/projects/", {"name": "Secret"}, format="json")
        self.assertEqual(created.status_code, 403)

        workers = lead_client.post("/api/workers/", {"name": "Ada"}, format="json")
        self.assertEqual(workers.status_code, 403)

        stock = lead_client.post("/api/stock-types/", {"name": "Cement"}, format="json")
        self.assertEqual(stock.status_code, 403)

        statuses = lead_client.post("/api/task-statuses/", {"name": "Blocked", "category": "todo"}, format="json")
        self.assertEqual(statuses.status_code, 403)

    def test_team_lead_can_report_and_move_only_their_team_tasks(self):
        lead_client, _lead = self._lead_client(self.team)
        own_task = create_task(
            self.company, self.project, self.owner, title="Own", team=self.team, status=self.todo
        )
        other_task = create_task(
            self.company, self.project, self.owner, title="Other", team=self.other_team, status=self.todo
        )
        unassigned = create_task(self.company, self.project, self.owner, title="Open", status=self.todo)

        own_move = lead_client.post(
            f"/api/tasks/{own_task.id}/move/",
            {"status": self.doing.id, "position": 0},
            format="json",
        )
        self.assertEqual(own_move.status_code, 200)

        other_move = lead_client.post(
            f"/api/tasks/{other_task.id}/move/",
            {"status": self.doing.id, "position": 0},
            format="json",
        )
        self.assertEqual(other_move.status_code, 403)

        open_move = lead_client.post(
            f"/api/tasks/{unassigned.id}/move/",
            {"status": self.doing.id, "position": 0},
            format="json",
        )
        self.assertEqual(open_move.status_code, 403)

        comment = lead_client.post(
            f"/api/tasks/{own_task.id}/comments/",
            {"body": "Slab is curing"},
            format="json",
        )
        self.assertEqual(comment.status_code, 201)

        other_comment = lead_client.post(
            f"/api/tasks/{other_task.id}/comments/",
            {"body": "Not your slab"},
            format="json",
        )
        self.assertEqual(other_comment.status_code, 403)

        create_task_denied = lead_client.post(
            "/api/tasks/",
            {"title": "Lead task", "project": self.project.id},
            format="json",
        )
        self.assertEqual(create_task_denied.status_code, 403)

        report = lead_client.post(
            "/api/site-reports/",
            {
                "workplace": self.project.id,
                "team": self.team.id,
                "task": own_task.id,
                "work_date": "2026-06-04",
                "days": "1.00",
                "quantity": "12.00",
            },
            format="json",
        )
        self.assertEqual(report.status_code, 201, report.data)

        other_report = lead_client.post(
            "/api/site-reports/",
            {
                "workplace": self.project.id,
                "team": self.other_team.id,
                "work_date": "2026-06-05",
                "days": "1.00",
                "quantity": "8.00",
            },
            format="json",
        )
        self.assertEqual(other_report.status_code, 400)

    def test_reorder_statuses_and_comments(self):
        ids = list(TaskStatus.objects.filter(company=self.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/task-statuses/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)

        task = create_task(self.company, self.project, self.owner, title="Inspect", status=self.todo)
        comment = self.client.post(
            f"/api/tasks/{task.id}/comments/",
            {"body": "Need photos"},
            format="json",
        )
        self.assertEqual(comment.status_code, 201)
        listed = self.client.get(f"/api/tasks/{task.id}/comments/")
        self.assertEqual(listed.data[0]["body"], "Need photos")

    def test_categories_can_be_added_and_used_on_a_status(self):
        created = self.client.post(
            "/api/task-categories/",
            {"name": "Waiting", "color": "#B9770E"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["color"], "#b9770e")
        status = self.client.post(
            "/api/task-statuses/",
            {"name": "On hold", "category": created.data["id"]},
            format="json",
        )
        self.assertEqual(status.status_code, 201)
        self.assertEqual(status.data["category_name"], "Waiting")
        blocked = self.client.delete(f"/api/task-categories/{created.data['id']}/")
        self.assertEqual(blocked.status_code, 400)
        ids = list(TaskCategory.objects.filter(company=self.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/task-categories/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)

    def test_phases_can_be_added_and_used_on_a_task(self):
        created = self.client.post("/api/task-phases/", {"name": "Close-out"}, format="json")
        self.assertEqual(created.status_code, 201)
        task = self.client.post(
            "/api/tasks/",
            {"title": "Handover", "project": self.project.id, "phase": created.data["id"]},
            format="json",
        )
        self.assertEqual(task.status_code, 201)
        self.assertEqual(task.data["phase_name"], "Close-out")
        listed = self.client.get(f"/api/tasks/?phase={created.data['id']}")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row["id"] for row in listed.data["results"]], [task.data["id"]])
        blocked = self.client.delete(f"/api/task-phases/{created.data['id']}/")
        self.assertEqual(blocked.status_code, 400)
        unused = TaskPhase.objects.get(company=self.company, name="Design")
        removed = self.client.delete(f"/api/task-phases/{unused.id}/")
        self.assertEqual(removed.status_code, 204)
        ids = list(TaskPhase.objects.filter(company=self.company).values_list("id", flat=True))
        ids.append(ids.pop(0))
        reordered = self.client.post("/api/task-phases/reorder/", {"ids": ids}, format="json")
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual([row["id"] for row in reordered.data], ids)
