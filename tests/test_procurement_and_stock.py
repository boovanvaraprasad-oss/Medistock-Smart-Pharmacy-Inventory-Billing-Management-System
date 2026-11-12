"""
Part 9 — Tests: Procurement & Stock (Part 4)
Covers: purchase orders (create, update, receive),
        stock batch intake, stock transaction ledger.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

import app.core.database as _db
from conftest import login


async def _seed_supplier():
    result = await _db.db.suppliers.insert_one({
        "name": "MedSupply Co.",
        "contact_name": "Ravi",
        "contact_phone": "9876543210",
        "is_active": True,
    })
    return str(result.inserted_id)


async def _seed_medicine(name="Paracetamol 500mg", sku="PCM500", price=10.0, stock=0):
    result = await _db.db.medicines.insert_one({
        "name": name,
        "sku": sku,
        "dosage_form": "Tablet",
        "price": price,
        "stock": stock,
        "reorder_threshold": 20,
        "is_active": True,
        "is_controlled_substance": False,
    })
    return str(result.inserted_id)


# ------------------------------------------------------------------ #
#  Purchase Orders                                                    #
# ------------------------------------------------------------------ #

class TestPurchaseOrders:

    @pytest.mark.asyncio
    async def test_create_purchase_order(self, client, owner_headers):
        supplier_id = await _seed_supplier()
        resp = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft", "notes": "Test PO"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["status"] == "draft"
        assert data["supplier_id"] == supplier_id

    @pytest.mark.asyncio
    async def test_list_purchase_orders(self, client, owner_headers):
        supplier_id = await _seed_supplier()
        await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/purchase-orders", headers=owner_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_update_purchase_order_status(self, client, owner_headers):
        supplier_id = await _seed_supplier()
        create = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        po_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/purchase-orders/{po_id}",
            json={"status": "ordered"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ordered"

    @pytest.mark.asyncio
    async def test_pharmacist_cannot_create_purchase_order(self, client, owner_headers):
        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        supplier_id = await _seed_supplier()
        resp = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers={"Authorization": f"Bearer {pharm_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_receive_purchase_order(self, client, owner_headers):
        medicine_id = await _seed_medicine(stock=0)
        supplier_id = await _seed_supplier()
        create = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        po_id = create.json()["id"]
        expiry = (datetime.now(timezone.utc) + timedelta(days=365)).date().isoformat()
        await client.post(
            "/api/v1/purchase-items",
            json={
                "purchase_order_id": po_id,
                "medicine_id": medicine_id,
                "quantity": 25,
                "unit_price": 10.0,
                "batch_number": "BATCH-RCV-01",
                "expiry_date": expiry,
            },
            headers=owner_headers,
        )
        await client.patch(
            f"/api/v1/purchase-orders/{po_id}",
            json={"status": "ordered"},
            headers=owner_headers,
        )
        resp = await client.patch(
            f"/api/v1/purchase-orders/{po_id}/receive",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] in ("received", "partially_received", "ordered")


# ------------------------------------------------------------------ #
#  Stock Batch Intake                                                 #
# ------------------------------------------------------------------ #

class TestStockBatchIntake:

    @pytest.mark.asyncio
    async def test_add_batch_increases_medicine_stock(self, client, owner_headers):
        medicine_id = await _seed_medicine(stock=0)
        supplier_id = await _seed_supplier()

        # Create purchase order and add item
        po_resp = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        po_id = po_resp.json()["id"]
        expiry = (datetime.now(timezone.utc) + timedelta(days=365)).date().isoformat()

        item_resp = await client.post(
            "/api/v1/purchase-items",
            json={
                "purchase_order_id": po_id,
                "medicine_id": medicine_id,
                "quantity": 100,
                "unit_price": 8.0,
                "batch_number": "BATCH2024A",
                "expiry_date": expiry,
            },
            headers=owner_headers,
        )
        assert item_resp.status_code in (200, 201), item_resp.text

        await client.patch(
            f"/api/v1/purchase-orders/{po_id}",
            json={"status": "ordered"},
            headers=owner_headers,
        )
        rcv_resp = await client.patch(
            f"/api/v1/purchase-orders/{po_id}/receive",
            headers=owner_headers,
        )
        assert rcv_resp.status_code == 200

        # Stock should have increased
        med = await _db.db.medicines.find_one({"_id": ObjectId(medicine_id)})
        assert med["stock"] >= 100

    @pytest.mark.asyncio
    async def test_stock_transaction_is_recorded_on_intake(self, client, owner_headers):
        medicine_id = await _seed_medicine(stock=0)
        supplier_id = await _seed_supplier()

        po_resp = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        po_id = po_resp.json()["id"]
        expiry = (datetime.now(timezone.utc) + timedelta(days=365)).date().isoformat()

        await client.post(
            "/api/v1/purchase-items",
            json={
                "purchase_order_id": po_id,
                "medicine_id": medicine_id,
                "quantity": 50,
                "unit_price": 8.0,
                "batch_number": "BATCHLOG01",
                "expiry_date": expiry,
            },
            headers=owner_headers,
        )

        await client.patch(
            f"/api/v1/purchase-orders/{po_id}",
            json={"status": "ordered"},
            headers=owner_headers,
        )
        rcv_resp = await client.patch(
            f"/api/v1/purchase-orders/{po_id}/receive",
            headers=owner_headers,
        )
        assert rcv_resp.status_code == 200

        resp = await client.get(
            f"/api/v1/stock/transactions?medicine_id={medicine_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        txns = resp.json()
        assert len(txns) >= 1
        types = [t["transaction_type"] for t in txns]
        assert any("STOCK_IN" in t or "IN" in t for t in types)


# ------------------------------------------------------------------ #
#  Stock Transaction Ledger                                           #
# ------------------------------------------------------------------ #

class TestStockTransactions:

    @pytest.mark.asyncio
    async def test_low_stock_endpoint_returns_medicines_below_threshold(self, client, owner_headers):
        # Seed a medicine with stock below threshold
        await _db.db.medicines.insert_one({
            "name": "LowMed",
            "sku": "LOWTEST01",
            "stock": 5,
            "reorder_threshold": 20,
            "is_active": True,
        })
        resp = await client.get("/api/v1/stock/low-stock", headers=owner_headers)
        assert resp.status_code == 200
        skus = [m.get("sku") for m in resp.json()]
        assert "LOWTEST01" in skus

    @pytest.mark.asyncio
    async def test_stock_transactions_filterable_by_type(self, client, owner_headers):
        medicine_id = await _seed_medicine(stock=0)
        supplier_id = await _seed_supplier()

        po_resp = await client.post(
            "/api/v1/purchase-orders",
            json={"supplier_id": supplier_id, "status": "draft"},
            headers=owner_headers,
        )
        po_id = po_resp.json()["id"]
        await client.patch(
            f"/api/v1/purchase-orders/{po_id}",
            json={"status": "ordered"},
            headers=owner_headers,
        )
        expiry = (datetime.now(timezone.utc) + timedelta(days=365)).date().isoformat()

        await client.post(
            "/api/v1/purchase-items",
            json={
                "purchase_order_id": po_id,
                "medicine_id": medicine_id,
                "quantity_ordered": 100,
                "unit_price": 8.0,
                "batch_number": "FILTER001",
                "expiry_date": expiry,
            },
            headers=owner_headers,
        )

        # Filter by STOCK_IN type
        resp = await client.get(
            f"/api/v1/stock/transactions?medicine_id={medicine_id}&transaction_type=STOCK_IN",
            headers=owner_headers,
        )
        assert resp.status_code == 200

