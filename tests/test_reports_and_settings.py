"""
Part 9 — Tests: Reports & Settings (Part 8)
Covers: billing settings, store settings, report endpoints,
        Excel/PDF export content-type checks.
"""

import pytest
from bson import ObjectId
from datetime import datetime, timedelta, timezone

import app.core.database as _db


async def _seed_medicine(sku="REP001", price=20.0, stock=100):
    result = await _db.db.medicines.insert_one({
        "name": "Report Med",
        "sku": sku,
        "dosage_form": "Tablet",
        "price": price,
        "stock": stock,
        "reorder_threshold": 10,
        "is_active": True,
        "is_controlled_substance": False,
    })
    return str(result.inserted_id)


# ------------------------------------------------------------------ #
#  Settings — Billing                                                 #
# ------------------------------------------------------------------ #

class TestBillingSettings:

    @pytest.mark.asyncio
    async def test_get_default_billing_settings(self, client, owner_headers):
        resp = await client.get("/api/v1/settings", headers=owner_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "default_tax_percentage" in data
        assert "invoice_prefix" in data

    @pytest.mark.asyncio
    async def test_owner_can_update_billing_settings(self, client, owner_headers):
        resp = await client.put(
            "/api/v1/settings",
            json={"default_tax_percentage": 18.0, "invoice_prefix": "RX"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_tax_percentage"] == 18.0
        assert data["invoice_prefix"] == "RX"

    @pytest.mark.asyncio
    async def test_tax_percentage_above_100_is_rejected(self, client, owner_headers):
        resp = await client.put(
            "/api/v1/settings",
            json={"default_tax_percentage": 110.0, "invoice_prefix": "INV"},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invoice_prefix_with_special_chars_rejected(self, client, owner_headers):
        resp = await client.put(
            "/api/v1/settings",
            json={"default_tax_percentage": 5.0, "invoice_prefix": "INV@#!"},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invoice_prefix_applied_to_new_bills(self, client, owner_headers):
        await client.put(
            "/api/v1/settings",
            json={"default_tax_percentage": 0.0, "invoice_prefix": "MEDX"},
            headers=owner_headers,
        )
        bill_resp = await client.post(
            "/api/v1/bills",
            json={"customer_name": "Test", "customer_phone": "1234567890"},
            headers=owner_headers,
        )
        assert bill_resp.status_code in (200, 201)
        assert bill_resp.json()["invoice_number"].startswith("MEDX")


# ------------------------------------------------------------------ #
#  Settings — Store Info                                              #
# ------------------------------------------------------------------ #

class TestStoreSettings:

    @pytest.mark.asyncio
    async def test_owner_can_update_store_settings(self, client, owner_headers):
        resp = await client.put(
            "/api/v1/settings/store",
            json={
                "store_name": "City Pharmacy",
                "address": "123 Main St",
                "phone": "9876543210",
                "email": "pharmacy@citypharm.com",
                "license_number": "LIC2024001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == "City Pharmacy"
        assert data["license_number"] == "LIC2024001"

    @pytest.mark.asyncio
    async def test_get_store_settings(self, client, owner_headers):
        await client.put(
            "/api/v1/settings/store",
            json={"store_name": "My Pharmacy", "address": "", "phone": "", "email": "", "license_number": ""},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/settings/store", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["store_name"] == "My Pharmacy"

    @pytest.mark.asyncio
    async def test_invalid_store_email_rejected(self, client, owner_headers):
        resp = await client.put(
            "/api/v1/settings/store",
            json={"store_name": "X", "address": "", "phone": "", "email": "not-an-email", "license_number": ""},
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ------------------------------------------------------------------ #
#  Reports — Endpoint Availability & Exports                          #
# ------------------------------------------------------------------ #

class TestReports:

    @pytest.mark.asyncio
    async def test_sales_report_excel_export(self, client, owner_headers):
        resp = await client.get(
            "/api/v1/reports/sales/export?format=xlsx&period=day",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "spreadsheet" in ct or "excel" in ct or "octet-stream" in ct

    @pytest.mark.asyncio
    async def test_sales_report_pdf_export(self, client, owner_headers):
        resp = await client.get(
            "/api/v1/reports/sales/export?format=pdf&period=day",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "pdf" in ct

    @pytest.mark.asyncio
    async def test_inventory_report_excel_export(self, client, owner_headers):
        resp = await client.get(
            "/api/v1/reports/inventory/export?format=xlsx",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "spreadsheet" in ct or "excel" in ct or "octet-stream" in ct

    @pytest.mark.asyncio
    async def test_inventory_report_pdf_export(self, client, owner_headers):
        resp = await client.get(
            "/api/v1/reports/inventory/export?format=pdf",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "pdf" in ct

    @pytest.mark.asyncio
    async def test_pharmacist_cannot_access_reports(self, client, owner_headers):
        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        from conftest import login
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        resp = await client.get(
            "/api/v1/reports/sales/export?format=xlsx&period=day",
            headers={"Authorization": f"Bearer {pharm_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_compliance_officer_can_access_reports(self, client, owner_headers):
        await client.post(
            "/api/v1/users",
            json={"email": "comp@medistock.com", "password": "CompPass1!", "role": "compliance_officer"},
            headers=owner_headers,
        )
        from conftest import login
        comp_token = await login(client, "comp@medistock.com", "CompPass1!")
        resp = await client.get(
            "/api/v1/reports/sales/export?format=xlsx&period=day",
            headers={"Authorization": f"Bearer {comp_token}"},
        )
        assert resp.status_code == 200

