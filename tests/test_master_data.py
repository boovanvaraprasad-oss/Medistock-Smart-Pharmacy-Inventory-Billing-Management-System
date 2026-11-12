"""
Part 9 — Tests: Master Data (Part 3)
Covers: categories, manufacturers, suppliers, units, medicines CRUD.
        Only the owner may delete — other roles get 403.
"""

import pytest
from conftest import login


# ------------------------------------------------------------------ #
#  Categories                                                         #
# ------------------------------------------------------------------ #

class TestCategories:

    @pytest.mark.asyncio
    async def test_create_category(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/categories",
            json={"name": "Antibiotics"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["name"].lower() == "antibiotics"

    @pytest.mark.asyncio
    async def test_list_categories(self, client, owner_headers):
        await client.post("/api/v1/categories", json={"name": "Vitamins"}, headers=owner_headers)
        resp = await client.get("/api/v1/categories", headers=owner_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_duplicate_category_name_rejected(self, client, owner_headers):
        await client.post("/api/v1/categories", json={"name": "Antibiotics"}, headers=owner_headers)
        resp = await client.post("/api/v1/categories", json={"name": "Antibiotics"}, headers=owner_headers)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_category_owner_only(self, client, owner_headers):
        create = await client.post("/api/v1/categories", json={"name": "Temp"}, headers=owner_headers)
        cat_id = create.json()["id"]

        # Create pharmacist and try to delete
        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        pharm_headers = {"Authorization": f"Bearer {pharm_token}"}
        resp = await client.delete(f"/api/v1/categories/{cat_id}", headers=pharm_headers)
        assert resp.status_code == 403

        # Owner can delete
        resp = await client.delete(f"/api/v1/categories/{cat_id}", headers=owner_headers)
        assert resp.status_code == 200


# ------------------------------------------------------------------ #
#  Manufacturers                                                      #
# ------------------------------------------------------------------ #

class TestManufacturers:

    @pytest.mark.asyncio
    async def test_create_manufacturer(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/manufacturers",
            json={"name": "Sun Pharma"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["name"].lower() == "sun pharma"

    @pytest.mark.asyncio
    async def test_update_manufacturer(self, client, owner_headers):
        create = await client.post(
            "/api/v1/manufacturers",
            json={"name": "Old Name"},
            headers=owner_headers,
        )
        mfr_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/manufacturers/{mfr_id}",
            json={"name": "New Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"].lower() == "new name"


# ------------------------------------------------------------------ #
#  Suppliers                                                          #
# ------------------------------------------------------------------ #

class TestSuppliers:

    @pytest.mark.asyncio
    async def test_create_supplier(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "MedSupply Co.",
                "phone": "9876543210",
                "email": "ravi@medsupply.com",
            },
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["name"].lower() == "medsupply co."

    @pytest.mark.asyncio
    async def test_list_suppliers(self, client, owner_headers):
        await client.post(
            "/api/v1/suppliers",
            json={"name": "Alpha Pharma", "phone": "1234567890"},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/suppliers", headers=owner_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ------------------------------------------------------------------ #
#  Units                                                              #
# ------------------------------------------------------------------ #

class TestUnits:

    @pytest.mark.asyncio
    async def test_create_unit(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/units",
            json={"name": "Tablet", "abbreviation": "Tab"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["name"].lower() == "tablet"

    @pytest.mark.asyncio
    async def test_duplicate_unit_rejected(self, client, owner_headers):
        await client.post("/api/v1/units", json={"name": "Tablet", "abbreviation": "Tab"}, headers=owner_headers)
        resp = await client.post("/api/v1/units", json={"name": "Tablet", "abbreviation": "Tab"}, headers=owner_headers)
        assert resp.status_code == 409


# ------------------------------------------------------------------ #
#  Medicines                                                          #
# ------------------------------------------------------------------ #

async def _create_medicine_prerequisites(client, owner_headers):
    """Create category, manufacturer, unit, supplier and return their IDs."""
    cat = await client.post("/api/v1/categories", json={"name": "Antibiotics"}, headers=owner_headers)
    mfr = await client.post("/api/v1/manufacturers", json={"name": "Sun Pharma"}, headers=owner_headers)
    unit = await client.post("/api/v1/units", json={"name": "Tablet", "abbreviation": "Tab"}, headers=owner_headers)
    supplier = await client.post(
        "/api/v1/suppliers",
        json={"name": "MedSupply", "phone": "1234567890"},
        headers=owner_headers,
    )
    return {
        "category_id": cat.json()["id"],
        "manufacturer_id": mfr.json()["id"],
        "unit_id": unit.json()["id"],
        "supplier_id": supplier.json()["id"],
    }


class TestMedicines:

    @pytest.mark.asyncio
    async def test_create_medicine(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        resp = await client.post(
            "/api/v1/medicines",
            json={
                "name": "Amoxicillin 500mg",
                "sku": "AMX500",
                "dosage_form": "Tablet",
                "price": 12.50,
                "reorder_threshold": 50,
                "is_controlled_substance": False,
                **ids,
            },
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "Amoxicillin 500mg"
        assert data["sku"] == "AMX500"

    @pytest.mark.asyncio
    async def test_list_medicines(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        await client.post(
            "/api/v1/medicines",
            json={"name": "Paracetamol 500mg", "sku": "PCM500", "dosage_form": "Tablet", "price": 5.0, "reorder_threshold": 20, "is_controlled_substance": False, **ids},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/medicines", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_medicine_by_name(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        await client.post(
            "/api/v1/medicines",
            json={"name": "Metformin 500mg", "sku": "MET500", "dosage_form": "Tablet", "price": 8.0, "reorder_threshold": 30, "is_controlled_substance": False, **ids},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/medicines?search=Metformin", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_duplicate_sku_rejected(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        payload = {"name": "Med A", "sku": "DUPE001", "dosage_form": "Tablet", "price": 5.0, "reorder_threshold": 10, "is_controlled_substance": False, **ids}
        await client.post("/api/v1/medicines", json=payload, headers=owner_headers)
        payload["name"] = "Med B"
        resp = await client.post("/api/v1/medicines", json=payload, headers=owner_headers)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_update_medicine_price(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        create = await client.post(
            "/api/v1/medicines",
            json={"name": "Aspirin 100mg", "sku": "ASP100", "dosage_form": "Tablet", "price": 3.0, "reorder_threshold": 10, "is_controlled_substance": False, **ids},
            headers=owner_headers,
        )
        med_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/medicines/{med_id}",
            json={"price": 4.5},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["price"] == 4.5

    @pytest.mark.asyncio
    async def test_pharmacist_cannot_delete_medicine(self, client, owner_headers):
        ids = await _create_medicine_prerequisites(client, owner_headers)
        create = await client.post(
            "/api/v1/medicines",
            json={"name": "Aspirin 100mg", "sku": "ASP100", "dosage_form": "Tablet", "price": 3.0, "reorder_threshold": 10, "is_controlled_substance": False, **ids},
            headers=owner_headers,
        )
        med_id = create.json()["id"]

        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        resp = await client.delete(
            f"/api/v1/medicines/{med_id}",
            headers={"Authorization": f"Bearer {pharm_token}"},
        )
        assert resp.status_code == 403

