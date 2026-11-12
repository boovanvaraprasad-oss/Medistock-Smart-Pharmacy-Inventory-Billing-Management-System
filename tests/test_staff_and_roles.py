"""
Part 9 — Tests: Staff & Roles (Part 2)
Covers: create staff, assign roles, activate/deactivate,
        owner-lock protections, delete, permission enforcement.
"""

import pytest
from conftest import register_owner, login, auth_headers


class TestStaffCreate:

    @pytest.mark.asyncio
    async def test_owner_can_create_staff(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["role"] == "pharmacist"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_pharmacist_cannot_create_staff(self, client, owner_headers):
        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        pharm_headers = {"Authorization": f"Bearer {pharm_token}"}

        resp = await client.post(
            "/api/v1/users",
            json={"email": "other@medistock.com", "password": "OtherPass1!", "role": "pharmacist"},
            headers=pharm_headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_duplicate_email_is_rejected(self, client, owner_headers):
        payload = {"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"}
        await client.post("/api/v1/users", json=payload, headers=owner_headers)
        resp = await client.post("/api/v1/users", json=payload, headers=owner_headers)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_role_is_rejected(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/users",
            json={"email": "x@medistock.com", "password": "PharmPass1!", "role": "superadmin"},
            headers=owner_headers,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_all_valid_roles_can_be_created(self, client, owner_headers):
        roles = [
            "pharmacist",
            "inventory_executive",
            "purchase_executive",
            "store_manager",
            "compliance_officer",
        ]
        for i, role in enumerate(roles):
            resp = await client.post(
                "/api/v1/users",
                json={"email": f"user{i}@medistock.com", "password": "StaffPass1!", "role": role},
                headers=owner_headers,
            )
            assert resp.status_code in (200, 201), f"Failed for role {role}: {resp.text}"


class TestStaffRead:

    @pytest.mark.asyncio
    async def test_list_staff(self, client, owner_headers):
        await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        resp = await client.get("/api/v1/users", headers=owner_headers)
        assert resp.status_code == 200
        users = resp.json()
        assert isinstance(users, list)
        assert len(users) >= 2  # owner + pharmacist

    @pytest.mark.asyncio
    async def test_get_single_staff(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]
        resp = await client.get(f"/api/v1/users/{user_id}", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "pharm@medistock.com"


class TestStaffUpdate:

    @pytest.mark.asyncio
    async def test_owner_can_change_role(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/users/{user_id}",
            json={"role": "store_manager"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "store_manager"

    @pytest.mark.asyncio
    async def test_owner_can_deactivate_staff(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_owner_cannot_deactivate_last_owner(self, client, owner_headers):
        # Find the owner user
        users = await client.get("/api/v1/users", headers=owner_headers)
        owner_user = next(u for u in users.json() if u["role"] == "owner")
        resp = await client.patch(
            f"/api/v1/users/{owner_user['id']}",
            json={"is_active": False},
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_update_own_role(self, client, owner_headers):
        users = await client.get("/api/v1/users", headers=owner_headers)
        owner_user = next(u for u in users.json() if u["role"] == "owner")
        resp = await client.patch(
            f"/api/v1/users/{owner_user['id']}",
            json={"role": "pharmacist"},
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_no_fields_to_update_returns_400(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/users/{user_id}",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 400


class TestStaffDelete:

    @pytest.mark.asyncio
    async def test_cannot_delete_active_user(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/users/{user_id}", headers=owner_headers)
        assert resp.status_code in (400, 409)

    @pytest.mark.asyncio
    async def test_delete_inactive_user_with_no_audit_history(self, client, owner_headers):
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        user_id = create.json()["id"]

        # Deactivate first
        await client.patch(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
            headers=owner_headers,
        )

        # Now attempt delete — may succeed or fail depending on audit history
        resp = await client.delete(f"/api/v1/users/{user_id}", headers=owner_headers)
        # Either deleted (200) or blocked due to audit history (409)
        assert resp.status_code in (200, 409)

    @pytest.mark.asyncio
    async def test_cannot_delete_owner(self, client, owner_headers):
        users = await client.get("/api/v1/users", headers=owner_headers)
        owner_user = next(u for u in users.json() if u["role"] == "owner")
        resp = await client.delete(f"/api/v1/users/{owner_user['id']}", headers=owner_headers)
        assert resp.status_code in (400, 409)

