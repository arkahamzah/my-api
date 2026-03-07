"""
Integration tests: RBAC untuk Tenants endpoints.

Permission matrix:
  ADMIN  → semua (ADMIN_PANEL untuk write, USER_READ untuk read)
  MEMBER → hanya read (USER_READ)
  VIEWER → hanya read (USER_READ)
"""

import pytest
from httpx import AsyncClient

TENANTS_URL = "/api/v1/tenants"
TENANT_BODY = {
    "name": "Acme Corp",
    "slug": "acme-corp",
    "owner_email": "owner@acme.com",
    "plan": "free",
}


# ─── Helper ──────────────────────────────────────────────────────────────────

async def _create_tenant(client: AsyncClient, headers: dict, slug: str = "acme-corp") -> str:
    body = {**TENANT_BODY, "slug": slug}
    resp = await client.post(TENANTS_URL, json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ─── Unauthenticated ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tenants_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(TENANTS_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_tenant_unauthenticated(client: AsyncClient) -> None:
    resp = await client.post(TENANTS_URL, json=TENANT_BODY)
    assert resp.status_code == 401


# ─── VIEWER & MEMBER: tidak boleh write ──────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tenants_member_forbidden(client: AsyncClient, member_headers: dict) -> None:
    resp = await client.get(TENANTS_URL, headers=member_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_tenants_viewer_forbidden(client: AsyncClient, viewer_headers: dict) -> None:
    resp = await client.get(TENANTS_URL, headers=viewer_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_tenant_member_forbidden(client: AsyncClient, member_headers: dict) -> None:
    resp = await client.post(TENANTS_URL, json=TENANT_BODY, headers=member_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_tenant_viewer_forbidden(client: AsyncClient, viewer_headers: dict) -> None:
    resp = await client.post(TENANTS_URL, json=TENANT_BODY, headers=viewer_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_tenant_member_forbidden(
    client: AsyncClient, admin_headers: dict, member_headers: dict
) -> None:
    tenant_id = await _create_tenant(client, admin_headers)
    resp = await client.patch(
        f"{TENANTS_URL}/{tenant_id}", json={"name": "Baru"}, headers=member_headers
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_tenant_member_forbidden(
    client: AsyncClient, admin_headers: dict, member_headers: dict
) -> None:
    tenant_id = await _create_tenant(client, admin_headers, slug="to-delete-member")
    resp = await client.delete(f"{TENANTS_URL}/{tenant_id}", headers=member_headers)
    assert resp.status_code == 403


# ─── VIEWER & MEMBER: boleh read ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_tenant_member(
    client: AsyncClient, admin_headers: dict, member_headers: dict
) -> None:
    tenant_id = await _create_tenant(client, admin_headers)
    resp = await client.get(f"{TENANTS_URL}/{tenant_id}", headers=member_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == tenant_id


@pytest.mark.asyncio
async def test_get_tenant_viewer(
    client: AsyncClient, admin_headers: dict, viewer_headers: dict
) -> None:
    tenant_id = await _create_tenant(client, admin_headers)
    resp = await client.get(f"{TENANTS_URL}/{tenant_id}", headers=viewer_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_tenant_by_slug_member(
    client: AsyncClient, admin_headers: dict, member_headers: dict
) -> None:
    await _create_tenant(client, admin_headers)
    resp = await client.get(f"{TENANTS_URL}/slug/acme-corp", headers=member_headers)
    assert resp.status_code == 200
    assert resp.json()["slug"] == "acme-corp"


@pytest.mark.asyncio
async def test_get_tenant_by_slug_viewer(
    client: AsyncClient, admin_headers: dict, viewer_headers: dict
) -> None:
    await _create_tenant(client, admin_headers)
    resp = await client.get(f"{TENANTS_URL}/slug/acme-corp", headers=viewer_headers)
    assert resp.status_code == 200


# ─── ADMIN: boleh semua ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tenants_admin(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.get(TENANTS_URL, headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_tenant_admin(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.post(TENANTS_URL, json=TENANT_BODY, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "acme-corp"


@pytest.mark.asyncio
async def test_update_tenant_admin(client: AsyncClient, admin_headers: dict) -> None:
    tenant_id = await _create_tenant(client, admin_headers)
    resp = await client.patch(
        f"{TENANTS_URL}/{tenant_id}", json={"name": "Nama Baru"}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nama Baru"


@pytest.mark.asyncio
async def test_delete_tenant_admin(client: AsyncClient, admin_headers: dict) -> None:
    tenant_id = await _create_tenant(client, admin_headers, slug="to-delete")
    resp = await client.delete(f"{TENANTS_URL}/{tenant_id}", headers=admin_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_tenant_not_found(client: AsyncClient, admin_headers: dict) -> None:
    fake_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    resp = await client.get(f"{TENANTS_URL}/{fake_id}", headers=admin_headers)
    assert resp.status_code == 404