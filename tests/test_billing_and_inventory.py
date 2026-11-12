"""
Part 9 — Tests: Billing & Inventory Control (Parts 5 & 6)
Covers: create bill, add items, complete bill, payment validation,
        FEFO stock deduction, bill returns, stock adjustments,
        low-stock and expiry alerts.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

import app.core.database as _db


# ------------------------------------------------------------------ #
#  Shared helpers                                                     #
# ------------------------------------------------------------------ #

async def _seed_medicine(name="Paracetamol 500mg", sku="PCM500", price=10.0, stock=100, reorder_threshold=20):
    """Insert a medicine document directly into the test DB and return its id."""
    result = await _db.db.medicines.insert_one({
        "name": name,
        "sku": sku,
        "dosage_form": "Tablet",
        "price": price,
        "stock": stock,
        "reorder_threshold": reorder_threshold,
        "is_active": True,
        "is_controlled_substance": False,
    })
    return str(result.inserted_id)


async def _seed_batch(medicine_id: str, quantity: int, days_until_expiry: int = 180, batch_number="BATCH001"):
    """Insert a stock batch directly into the test DB and return its id."""
    expiry = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)
    result = await _db.db.stock_batches.insert_one({
        "medicine_id": ObjectId(medicine_id),
        "batch_number": batch_number,
        "quantity": quantity,
        "expiry_date": expiry,
        "is_active": True,
    })
    return str(result.inserted_id)


async def _create_draft_bill(client, owner_headers, customer_name="Test Customer", customer_phone="9876543210"):
    resp = await client.post(
        "/api/v1/bills",
        json={"customer_name": customer_name, "customer_phone": customer_phone},
        headers=owner_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


async def _add_bill_item(client, owner_headers, bill_id: str, medicine_id: str, quantity: int):
    resp = await client.post(
        "/api/v1/bills/items",
        json={"bill_id": bill_id, "medicine_id": medicine_id, "quantity": quantity},
        headers=owner_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ------------------------------------------------------------------ #
#  Billing — Draft Bill                                               #
# ------------------------------------------------------------------ #

class TestBillingDraft:

    @pytest.mark.asyncio
    async def test_create_draft_bill(self, client, owner_headers):
        bill = await _create_draft_bill(client, owner_headers)
        assert bill["status"] == "draft"
        assert bill["payment_status"] == "pending"
        assert bill["invoice_number"].startswith("INV")

    @pytest.mark.asyncio
    async def test_add_item_to_bill(self, client, owner_headers):
        medicine_id = await _seed_medicine()
        await _seed_batch(medicine_id, quantity=50)

        bill = await _create_draft_bill(client, owner_headers)
        item = await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=5)
        assert item["quantity"] == 5
        assert item["unit_price"] == 10.0
        assert item["total_price"] == 50.0

    @pytest.mark.asyncio
    async def test_update_bill_item_quantity(self, client, owner_headers):
        medicine_id = await _seed_medicine()
        await _seed_batch(medicine_id, quantity=50)

        bill = await _create_draft_bill(client, owner_headers)
        item = await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=5)

        resp = await client.patch(
            f"/api/v1/bills/items/{item['id']}",
            json={"quantity": 10},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 10

    @pytest.mark.asyncio
    async def test_delete_bill_item(self, client, owner_headers):
        medicine_id = await _seed_medicine()
        await _seed_batch(medicine_id, quantity=50)

        bill = await _create_draft_bill(client, owner_headers)
        item = await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=3)

        resp = await client.delete(f"/api/v1/bills/items/{item['id']}", headers=owner_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_cannot_complete_bill_with_no_items(self, client, owner_headers):
        bill = await _create_draft_bill(client, owner_headers)
        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 500.0},
            headers=owner_headers,
        )
        assert resp.status_code == 400


# ------------------------------------------------------------------ #
#  Billing — Complete Bill & Payment                                  #
# ------------------------------------------------------------------ #

class TestBillingComplete:

    @pytest.mark.asyncio
    async def test_complete_bill_with_cash_payment(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=50.0, stock=100)
        await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=2)

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 100.0},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["payment_status"] == "paid"
        assert data["payment_method"] == "cash"
        assert data["total_amount"] == 100.0
        assert data["change_due"] == 0.0

    @pytest.mark.asyncio
    async def test_cash_payment_with_change(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=50.0, stock=100)
        await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=1)

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 100.0},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["change_due"] == 50.0

    @pytest.mark.asyncio
    async def test_underpayment_is_rejected(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=100.0, stock=50)
        await _seed_batch(medicine_id, quantity=50)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=1)

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 50.0},
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upi_exact_amount_required(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=100.0, stock=50)
        await _seed_batch(medicine_id, quantity=50)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=1)

        # UPI with wrong amount
        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "upi", "amount_received": 150.0},
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_payment_method_rejected(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=50.0, stock=100)
        await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=1)

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "bitcoin", "amount_received": 50.0},
            headers=owner_headers,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_stock_is_deducted_on_bill_completion(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=100)
        await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=5)

        await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 50.0},
            headers=owner_headers,
        )

        med = await _db.db.medicines.find_one({"_id": ObjectId(medicine_id)})
        assert med["stock"] == 95

    @pytest.mark.asyncio
    async def test_cannot_complete_already_completed_bill(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=100)
        await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=1)

        await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 10.0},
            headers=owner_headers,
        )

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 10.0},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_insufficient_stock_prevents_bill_completion(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=5)
        await _seed_batch(medicine_id, quantity=5)

        bill = await _create_draft_bill(client, owner_headers)
        resp = await client.post(
            "/api/v1/bills/items",
            json={"bill_id": bill["id"], "medicine_id": medicine_id, "quantity": 10},
            headers=owner_headers,
        )
        assert resp.status_code == 400


# ------------------------------------------------------------------ #
#  FEFO — First Expiry First Out                                      #
# ------------------------------------------------------------------ #

class TestFEFO:

    @pytest.mark.asyncio
    async def test_fefo_deducts_earliest_expiry_batch_first(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=200)

        # Batch that expires sooner
        early_id = await _seed_batch(medicine_id, quantity=50, days_until_expiry=30, batch_number="EARLY001")
        # Batch that expires later
        await _seed_batch(medicine_id, quantity=150, days_until_expiry=180, batch_number="LATE001")

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=30)

        await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 300.0},
            headers=owner_headers,
        )

        # Early batch should have been deducted first
        early_batch = await _db.db.stock_batches.find_one({"_id": ObjectId(early_id)})
        assert early_batch["quantity"] == 20  # 50 - 30 = 20

    @pytest.mark.asyncio
    async def test_expired_batch_is_not_used_for_billing(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=50)
        # Insert an already-expired batch
        expired_at = datetime.now(timezone.utc) - timedelta(days=1)
        await _db.db.stock_batches.insert_one({
            "medicine_id": ObjectId(medicine_id),
            "batch_number": "EXPIRED001",
            "quantity": 50,
            "expiry_date": expired_at,
            "is_active": True,
        })

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=10)

        resp = await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 100.0},
            headers=owner_headers,
        )
        # Should fail — only expired batch stock available
        assert resp.status_code == 400


# ------------------------------------------------------------------ #
#  Bill Returns                                                       #
# ------------------------------------------------------------------ #

class TestBillReturns:

    @pytest.mark.asyncio
    async def test_return_stock_from_completed_bill(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=100)
        batch_id = await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)
        await _add_bill_item(client, owner_headers, bill["id"], medicine_id, quantity=5)
        await client.patch(
            f"/api/v1/bills/{bill['id']}/complete",
            json={"payment_method": "cash", "amount_received": 50.0},
            headers=owner_headers,
        )

        # Return 2 units
        resp = await client.post(
            f"/api/v1/bills/{bill['id']}/returns",
            json={"batch_id": batch_id, "quantity": 2, "reason": "Customer changed mind"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)

        # Batch stock should be restored
        batch = await _db.db.stock_batches.find_one({"_id": ObjectId(batch_id)})
        assert batch["quantity"] == 97  # 100 - 5 + 2 = 97

    @pytest.mark.asyncio
    async def test_cannot_return_from_draft_bill(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=100)
        batch_id = await _seed_batch(medicine_id, quantity=100)

        bill = await _create_draft_bill(client, owner_headers)

        resp = await client.post(
            f"/api/v1/bills/{bill['id']}/returns",
            json={"batch_id": batch_id, "quantity": 1, "reason": "Test"},
            headers=owner_headers,
        )
        assert resp.status_code in (400, 404, 409)


# ------------------------------------------------------------------ #
#  Stock Adjustments                                                  #
# ------------------------------------------------------------------ #

class TestStockAdjustments:

    @pytest.mark.asyncio
    async def test_positive_stock_adjustment(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=50)
        batch_id = await _seed_batch(medicine_id, quantity=50)

        # Create inventory_executive to do adjustments
        await client.post(
            "/api/v1/users",
            json={"email": "inv@medistock.com", "password": "InvPass123!", "role": "inventory_executive"},
            headers=owner_headers,
        )
        from conftest import login
        inv_token = await login(client, "inv@medistock.com", "InvPass123!")
        inv_headers = {"Authorization": f"Bearer {inv_token}"}

        resp = await client.post(
            "/api/v1/stock/adjustments",
            json={
                "medicine_id": medicine_id,
                "batch_id": batch_id,
                "quantity_change": 10,
                "reason": "Stock count correction",
            },
            headers=inv_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["new_batch_quantity"] == 60

    @pytest.mark.asyncio
    async def test_negative_adjustment_cannot_go_below_zero(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=10)
        batch_id = await _seed_batch(medicine_id, quantity=10)

        resp = await client.post(
            "/api/v1/stock/adjustments",
            json={
                "medicine_id": medicine_id,
                "batch_id": batch_id,
                "quantity_change": -20,
                "reason": "Test",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_adjustment_requires_reason(self, client, owner_headers):
        medicine_id = await _seed_medicine(price=10.0, stock=10)
        batch_id = await _seed_batch(medicine_id, quantity=10)

        resp = await client.post(
            "/api/v1/stock/adjustments",
            json={
                "medicine_id": medicine_id,
                "batch_id": batch_id,
                "quantity_change": 5,
                "reason": "   ",
            },
            headers=owner_headers,
        )
        assert resp.status_code in (400, 422)


# ------------------------------------------------------------------ #
#  Low-Stock & Expiry Alerts (Notifications)                          #
# ------------------------------------------------------------------ #

class TestInventoryAlerts:

    @pytest.mark.asyncio
    async def test_low_stock_alert_is_raised(self, client, owner_headers):
        # Seed a medicine with stock below threshold
        await _seed_medicine(name="LowMed", sku="LOW001", stock=5, reorder_threshold=20)

        resp = await client.get("/api/v1/notifications", headers=owner_headers)
        assert resp.status_code == 200
        data = resp.json()
        types = [item["type"] for item in data["items"]]
        assert "low_stock" in types or "out_of_stock" in types

    @pytest.mark.asyncio
    async def test_out_of_stock_alert_is_raised(self, client, owner_headers):
        await _seed_medicine(name="EmptyMed", sku="EMP001", stock=0, reorder_threshold=10)

        resp = await client.get("/api/v1/notifications", headers=owner_headers)
        assert resp.status_code == 200
        types = [item["type"] for item in resp.json()["items"]]
        assert "out_of_stock" in types

    @pytest.mark.asyncio
    async def test_expiring_batch_alert_is_raised(self, client, owner_headers):
        medicine_id = await _seed_medicine()
        # Batch expiring in 10 days (within 31-day alert window)
        await _seed_batch(medicine_id, quantity=20, days_until_expiry=10)

        resp = await client.get("/api/v1/notifications", headers=owner_headers)
        assert resp.status_code == 200
        types = [item["type"] for item in resp.json()["items"]]
        assert "expiring_batch" in types

    @pytest.mark.asyncio
    async def test_expired_batch_alert_is_critical(self, client, owner_headers):
        medicine_id = await _seed_medicine()
        # Batch already expired
        await _seed_batch(medicine_id, quantity=5, days_until_expiry=-5)

        resp = await client.get("/api/v1/notifications", headers=owner_headers)
        assert resp.status_code == 200
        critical = [i for i in resp.json()["items"] if i["type"] == "expired_batch"]
        assert len(critical) >= 1
        assert critical[0]["priority"] == "critical"

    @pytest.mark.asyncio
    async def test_well_stocked_medicine_has_no_alert(self, client, owner_headers):
        await _seed_medicine(name="GoodMed", sku="GOOD001", stock=200, reorder_threshold=20)

        resp = await client.get("/api/v1/notifications", headers=owner_headers)
        assert resp.status_code == 200
        low_items = [i for i in resp.json()["items"] if i.get("sku") == "GOOD001"]
        assert len(low_items) == 0

    @pytest.mark.asyncio
    async def test_unread_count_decreases_after_marking_read(self, client, owner_headers):
        await _seed_medicine(name="LowMed2", sku="LOW002", stock=0, reorder_threshold=10)

        notif_resp = await client.get("/api/v1/notifications", headers=owner_headers)
        items = notif_resp.json()["items"]
        assert len(items) > 0
        notif_id = items[0]["id"]
        initial_unread = notif_resp.json()["unread_count"]

        mark_resp = await client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            json={"read": True},
            headers=owner_headers,
        )
        assert mark_resp.status_code == 200
        assert mark_resp.json()["unread_count"] < initial_unread

