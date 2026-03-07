"""
Integration tests — Auth Endpoints
"""
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.domain.value_objects.role import Role
from tests.helpers.in_memory_user_repo import InMemoryUserRepo
from tests.integration.conftest import TENANT_ID

pytestmark = pytest.mark.asyncio


async def _register(client, email, username, password, tenant=TENANT_ID):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
        headers={"X-Tenant-ID": tenant},
    )
    assert r.status_code == 201, r.text
    return r.json()

async def _login(client, email, password, tenant=TENANT_ID):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Tenant-ID": tenant},
    )
    assert r.status_code == 200, r.text
    return r.json()

async def _make_admin(user_repo: InMemoryUserRepo, user_id: str, tenant=TENANT_ID):
    user = await user_repo.get_by_id(UUID(user_id), tenant)
    user.change_role(Role.ADMIN)
    await user_repo.update(user)

def _bearer(tokens: dict, tenant=TENANT_ID) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}", "X-Tenant-ID": tenant}


class TestRegister:
    async def test_register_sukses(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "budi@example.com", "username": "budi", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "budi@example.com"
        assert data["username"] == "budi"
        assert data["role"] == "member"
        assert data["is_active"] is True
        assert data["tenant_id"] == TENANT_ID
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_email_duplikat(self, client: AsyncClient):
        await _register(client, "duplikat@example.com", "user1", "secret123")
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "duplikat@example.com", "username": "user2", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 409
        assert "sudah terdaftar" in resp.json()["detail"]

    async def test_register_username_duplikat(self, client: AsyncClient):
        await _register(client, "a@example.com", "samauser", "secret123")
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "b@example.com", "username": "samauser", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 409
        assert "sudah dipakai" in resp.json()["detail"]

    async def test_register_password_terlalu_pendek(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "xuser", "password": "short"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 422

    async def test_register_username_terlalu_pendek(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "ab", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 422

    async def test_register_email_tidak_valid(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "bukan-email", "username": "xuser", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 422

    async def test_register_tanpa_tenant_id_header(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "xuser", "password": "secret123"},
        )
        assert resp.status_code == 422

    async def test_register_isolasi_antar_tenant(self, client: AsyncClient):
        payload = {"email": "shared@example.com", "username": "shareduser", "password": "secret123"}
        r1 = await client.post("/api/v1/auth/register", json=payload, headers={"X-Tenant-ID": "tenant-A"})
        r2 = await client.post("/api/v1/auth/register", json=payload, headers={"X-Tenant-ID": "tenant-B"})
        assert r1.status_code == 201
        assert r2.status_code == 201


class TestLogin:
    async def test_login_sukses(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_password_salah(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": "salahpassword"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401

    async def test_login_email_tidak_terdaftar(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "tidakada@example.com", "password": "secret123"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401

    async def test_login_tenant_berbeda(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
            headers={"X-Tenant-ID": "tenant-lain"},
        )
        assert resp.status_code == 401

    async def test_login_tanpa_tenant_id_header(self, client: AsyncClient, registered_user: dict):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 422


class TestRefresh:
    async def test_refresh_sukses(self, client: AsyncClient, auth_tokens: dict):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_hasilkan_access_token_baru(self, client: AsyncClient, auth_tokens: dict):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"] != auth_tokens["access_token"]

    async def test_refresh_token_tidak_valid(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "ini.token.palsu"},
        )
        assert resp.status_code == 401

    async def test_refresh_dengan_access_token_ditolak(self, client: AsyncClient, auth_tokens: dict):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["access_token"]},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_sukses(self, client: AsyncClient, auth_headers: dict, registered_user: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert data["username"] == registered_user["username"]
        assert data["tenant_id"] == TENANT_ID

    async def test_me_tanpa_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 401

    async def test_me_token_tidak_valid(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token.palsu.sekali", "X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401

    async def test_me_tenant_tidak_sesuai_token(self, client: AsyncClient, auth_tokens: dict):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {auth_tokens['access_token']}",
                "X-Tenant-ID": "tenant-lain",
            },
        )
        assert resp.status_code == 403


class TestChangePassword:
    async def test_change_password_sukses(
        self, client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": "newpassword456"},
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_change_password_current_salah(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": "salah123xx", "new_password": "newpassword456"},
            headers=auth_headers,
        )
        assert resp.status_code == 401

    async def test_change_password_baru_terlalu_pendek(
        self, client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": "short"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_change_password_tanpa_auth(self, client: AsyncClient):
        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": "lama123456", "new_password": "baru123456"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401

    async def test_password_lama_tidak_bisa_login_lagi(
        self, client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": "newpassword456"},
            headers=auth_headers,
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401

    async def test_password_baru_bisa_login(
        self, client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        new_pass = "newpassword456"
        await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": new_pass},
            headers=auth_headers,
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": new_pass},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 200


class TestAdminEndpoints:
    async def test_list_users_sebagai_admin(
        self, client: AsyncClient, user_repo: InMemoryUserRepo, registered_user: dict
    ):
        admin_data = await _register(client, "admin@example.com", "adminuser", "adminpass123")
        await _make_admin(user_repo, admin_data["id"])
        admin_tokens = await _login(client, "admin@example.com", "adminpass123")

        resp = await client.get("/api/v1/auth/users", headers=_bearer(admin_tokens))
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "admin@example.com" in emails
        assert registered_user["email"] in emails

    async def test_list_users_sebagai_member_ditolak(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get("/api/v1/auth/users", headers=auth_headers)
        assert resp.status_code == 403

    async def test_list_users_tanpa_auth_ditolak(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/users", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 401

    async def test_change_role_sebagai_admin(
        self, client: AsyncClient, user_repo: InMemoryUserRepo, registered_user: dict
    ):
        admin_data = await _register(client, "admin2@example.com", "adminuser2", "adminpass123")
        await _make_admin(user_repo, admin_data["id"])
        admin_tokens = await _login(client, "admin2@example.com", "adminpass123")

        resp = await client.put(
            "/api/v1/auth/users/role",
            json={"user_id": registered_user["data"]["id"], "new_role": "viewer"},
            headers=_bearer(admin_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "viewer"

    async def test_change_role_sebagai_member_ditolak(
        self, client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        resp = await client.put(
            "/api/v1/auth/users/role",
            json={"user_id": registered_user["data"]["id"], "new_role": "viewer"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    async def test_change_role_tanpa_auth_ditolak(
        self, client: AsyncClient, registered_user: dict
    ):
        resp = await client.put(
            "/api/v1/auth/users/role",
            json={"user_id": registered_user["data"]["id"], "new_role": "viewer"},
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 401
