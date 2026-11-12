"""
Part 9 — Tests: Authentication & Security
Covers: register, login, JWT, logout, token refresh,
        lockout, change-password, login-history, protected routes.
"""

import pytest
import pytest_asyncio
from conftest import register_owner, login, auth_headers


# ------------------------------------------------------------------ #
#  Registration                                                        #
# ------------------------------------------------------------------ #

class TestRegistration:

    @pytest.mark.asyncio
    async def test_first_signup_becomes_owner(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["role"] == "owner"

    @pytest.mark.asyncio
    async def test_second_signup_is_rejected(self, client):
        await register_owner(client)
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "other@medistock.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_signup_rejects_non_medistock_email(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@gmail.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_signup_rejects_weak_password(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "owner@medistock.com", "password": "short"},
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_signup_rejects_missing_fields(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "owner@medistock.com"},
        )
        assert resp.status_code == 422


# ------------------------------------------------------------------ #
#  Login                                                              #
# ------------------------------------------------------------------ #

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, client):
        await register_owner(client)
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client):
        await register_owner(client)
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "WrongPass1!"},
        )
        assert resp.status_code in (401, 400)

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "ghost@medistock.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code in (401, 400)

    @pytest.mark.asyncio
    async def test_login_inactive_user_is_rejected(self, client, owner_headers):
        # Create a staff user then deactivate them
        create_resp = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        assert create_resp.status_code in (200, 201)
        user_id = create_resp.json()["id"]

        await client.patch(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
            headers=owner_headers,
        )

        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "pharm@medistock.com", "password": "PharmPass1!"},
        )
        assert resp.status_code in (400, 401)


# ------------------------------------------------------------------ #
#  JWT / Me                                                           #
# ------------------------------------------------------------------ #

class TestJWT:

    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client, owner_headers):
        resp = await client.get("/api/v1/auth/me", headers=owner_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "owner@medistock.com"
        assert data["role"] == "owner"

    @pytest.mark.asyncio
    async def test_protected_route_requires_token(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_is_rejected(self, client):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer notavalidtoken"},
        )
        assert resp.status_code == 401


# ------------------------------------------------------------------ #
#  Logout & Token Revocation                                          #
# ------------------------------------------------------------------ #

class TestLogout:

    @pytest.mark.asyncio
    async def test_logout_revokes_access_token(self, client):
        await register_owner(client)
        login_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        access_token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Logout
        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"access_token": access_token},
            headers=headers,
        )
        assert logout_resp.status_code in (200, 204)

        # Token should now be rejected
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_issues_new_access_token(self, client):
        await register_owner(client)
        login_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    @pytest.mark.asyncio
    async def test_invalid_refresh_token_is_rejected(self, client):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "notavalidrefreshtoken"},
        )
        assert resp.status_code in (400, 401)


# ------------------------------------------------------------------ #
#  Login Lockout                                                      #
# ------------------------------------------------------------------ #

class TestLoginLockout:

    @pytest.mark.asyncio
    async def test_lockout_after_five_failures(self, client):
        await register_owner(client)
        for _ in range(5):
            await client.post(
                "/api/v1/auth/token",
                data={"username": "owner@medistock.com", "password": "WrongPass!"},
            )
        # 6th attempt should be locked out (429)
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "WrongPass!"},
        )
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_correct_password_after_some_failures_still_works(self, client):
        """3 failures should not lock — correct password still works."""
        await register_owner(client)
        for _ in range(3):
            await client.post(
                "/api/v1/auth/token",
                data={"username": "owner@medistock.com", "password": "WrongPass!"},
            )
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        assert resp.status_code == 200


# ------------------------------------------------------------------ #
#  Change Password                                                    #
# ------------------------------------------------------------------ #

class TestChangePassword:

    @pytest.mark.asyncio
    async def test_change_password_success(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OwnerPass1!",
                "new_password": "NewOwnerPass2@",
            },
            headers=owner_headers,
        )
        assert resp.status_code in (200, 204)
        # Old password should no longer work
        old_login = await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        assert old_login.status_code in (400, 401)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_is_rejected(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongCurrent1!",
                "new_password": "NewOwnerPass2@",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_same_as_current_is_rejected(self, client, owner_headers):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "OwnerPass1!",
                "new_password": "OwnerPass1!",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 400


# ------------------------------------------------------------------ #
#  Login History                                                      #
# ------------------------------------------------------------------ #

class TestLoginHistory:

    @pytest.mark.asyncio
    async def test_login_history_is_recorded(self, client, owner_headers):
        # Perform another login to ensure there is at least one record
        await client.post(
            "/api/v1/auth/token",
            data={"username": "owner@medistock.com", "password": "OwnerPass1!"},
        )
        resp = await client.get(
            "/api/v1/auth/login-history",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_login_history_requires_permission(self, client, owner_headers):
        # Create a pharmacist (no login_log:read permission)
        create = await client.post(
            "/api/v1/users",
            json={"email": "pharm@medistock.com", "password": "PharmPass1!", "role": "pharmacist"},
            headers=owner_headers,
        )
        assert create.status_code in (200, 201)
        pharm_token = await login(client, "pharm@medistock.com", "PharmPass1!")
        pharm_headers = {"Authorization": f"Bearer {pharm_token}"}

        resp = await client.get(
            "/api/v1/auth/login-history",
            headers=pharm_headers,
        )
        assert resp.status_code == 403

