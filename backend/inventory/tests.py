from datetime import date
from decimal import Decimal

from django.test import TestCase

from companies.testing import auth_client, make_membership, make_user
from inventory.models import Location, StockItem, StockLot, StockType
from operations.models import Workplace


class InventoryApiTests(TestCase):
    def setUp(self):
        self.user = make_user("stock@example.com")
        self.membership = make_membership(self.user, "Yard")
        self.client = auth_client(self.user, self.membership.company)
        self.stock_type = StockType.objects.create(
            company=self.membership.company,
            name="Cement",
            requires_expiration=False,
        )
        self.item = StockItem.objects.create(
            company=self.membership.company,
            stock_type=self.stock_type,
            name="Portland",
            unit="bag",
        )
        self.warehouse = Location.objects.create(
            company=self.membership.company,
            name="Main yard",
            kind=Location.Kind.DEPOT,
        )

    def test_receive_transfer_and_consume_keep_quantities(self):
        received = self.client.post(
            "/api/stock-lots/",
            {
                "item": self.item.id,
                "location": self.warehouse.id,
                "quantity": "10.00",
                "received_on": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(received.status_code, 201)
        lot_id = received.data["id"]

        workplace = Workplace.objects.create(company=self.membership.company, name="Block A")
        site = Location.objects.create(
            company=self.membership.company,
            name="Block A",
            kind=Location.Kind.SITE,
            workplace=workplace,
        )
        transfer = self.client.post(
            "/api/stock-movements/",
            {
                "lot": lot_id,
                "kind": "transfer",
                "quantity": "4.00",
                "to_location": site.id,
                "happened_on": "2026-06-02",
            },
            format="json",
        )
        self.assertEqual(transfer.status_code, 201)
        self.assertEqual(transfer.data["workplace"], workplace.id)

        source = StockLot.objects.get(pk=lot_id)
        self.assertEqual(source.quantity, Decimal("6.00"))
        destination = StockLot.objects.get(location=site, item=self.item)
        self.assertEqual(destination.quantity, Decimal("4.00"))

        consume = self.client.post(
            "/api/stock-movements/",
            {
                "lot": destination.id,
                "kind": "consume",
                "quantity": "1.50",
                "workplace": workplace.id,
                "happened_on": "2026-06-03",
            },
            format="json",
        )
        self.assertEqual(consume.status_code, 201)
        destination.refresh_from_db()
        self.assertEqual(destination.quantity, Decimal("2.50"))

        too_much = self.client.post(
            "/api/stock-movements/",
            {
                "lot": destination.id,
                "kind": "consume",
                "quantity": "9.00",
                "workplace": workplace.id,
                "happened_on": "2026-06-03",
            },
            format="json",
        )
        self.assertEqual(too_much.status_code, 400)

    def test_expiration_is_required_only_when_the_type_asks_for_it(self):
        paint = StockType.objects.create(
            company=self.membership.company,
            name="Paint",
            requires_expiration=True,
        )
        item = StockItem.objects.create(
            company=self.membership.company,
            stock_type=paint,
            name="White",
            unit="can",
        )
        missing = self.client.post(
            "/api/stock-lots/",
            {
                "item": item.id,
                "location": self.warehouse.id,
                "quantity": "2.00",
                "received_on": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(missing.status_code, 400)

        dated = self.client.post(
            "/api/stock-lots/",
            {
                "item": item.id,
                "location": self.warehouse.id,
                "quantity": "2.00",
                "expires_on": "2026-07-01",
                "received_on": "2026-06-01",
            },
            format="json",
        )
        self.assertEqual(dated.status_code, 201)

        upcoming = self.client.get("/api/stock-lots/?expires_before=2026-08-01")
        self.assertEqual(upcoming.status_code, 200)
        self.assertEqual(len(upcoming.data["results"]), 1)
        self.assertEqual(upcoming.data["results"][0]["expires_on"], "2026-07-01")

    def test_adjust_cannot_go_negative(self):
        lot = StockLot.objects.create(
            item=self.item,
            location=self.warehouse,
            quantity=Decimal("3.00"),
            received_on=date(2026, 6, 1),
        )
        response = self.client.post(
            "/api/stock-movements/",
            {
                "lot": lot.id,
                "kind": "adjust",
                "quantity": "-5.00",
                "happened_on": "2026-06-04",
                "note": "Count was wrong",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        lot.refresh_from_db()
        self.assertEqual(lot.quantity, Decimal("3.00"))
