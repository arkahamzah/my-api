"""
Integration tests: RBAC untuk Tasks endpoints.

Permission matrix:
  ADMIN  → semua (TASK_CREATE, TASK_READ, TASK_UPDATE, TASK_DELETE)
  MEMBER → TASK_CREATE, TASK_READ, TASK_UPDATE, TASK_DELETE
  VIEWER → TASK_READ saja
"""

import pytest
from httpx import AsyncClient

TENANT_UUID = "11111111-1111-1111-1111-111111111111"
TASKS_URL = f"/api/v1/tenants/{TENANT_UUID}/tasks"
TASK_BODY = {"title": "Test Task", "description": "Deskripsi", "priority": "medium"}


# ─── Helper ──────────────────────────────────────────────────────────────────

async def _create_task(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(TASKS_URL, json=TASK_BODY, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ─── Unauthenticated ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tasks_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(TASKS_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_task_unauthenticated(client: AsyncClient) -> None:
    resp = await client.post(TASKS_URL, json=TASK_BODY)
    assert resp.status_code == 401


# ─── VIEWER: boleh READ, tidak boleh WRITE ───────────────────────────────────

@pytest.mark.asyncio
async def test_list_tasks_viewer(client: AsyncClient, viewer_headers: dict) -> None:
    resp = await client.get(TASKS_URL, headers=viewer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_task_viewer_forbidden(client: AsyncClient, viewer_headers: dict) -> None:
    resp = await client.post(TASKS_URL, json=TASK_BODY, headers=viewer_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_task_viewer_forbidden(
    client: AsyncClient, member_headers: dict, viewer_headers: dict
) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.patch(
        f"{TASKS_URL}/{task_id}", json={"title": "Diubah"}, headers=viewer_headers
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_task_status_viewer_forbidden(
    client: AsyncClient, member_headers: dict, viewer_headers: dict
) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.patch(
        f"{TASKS_URL}/{task_id}/status",
        json={"status": "in_progress"},
        headers=viewer_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_task_viewer_forbidden(
    client: AsyncClient, member_headers: dict, viewer_headers: dict
) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.delete(f"{TASKS_URL}/{task_id}", headers=viewer_headers)
    assert resp.status_code == 403


# ─── MEMBER: boleh semua CRUD ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tasks_member(client: AsyncClient, member_headers: dict) -> None:
    resp = await client.get(TASKS_URL, headers=member_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_task_member(client: AsyncClient, member_headers: dict) -> None:
    resp = await client.post(TASKS_URL, json=TASK_BODY, headers=member_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == TASK_BODY["title"]


@pytest.mark.asyncio
async def test_create_task_sets_created_by_current_user(
    client: AsyncClient, member_headers: dict
) -> None:
    resp = await client.post(TASKS_URL, json=TASK_BODY, headers=member_headers)
    assert resp.status_code == 201
    # created_by harus UUID valid (bukan SYSTEM_USER_ID lagi)
    created_by = resp.json().get("created_by")
    assert created_by is not None
    assert created_by != "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_get_task_member(client: AsyncClient, member_headers: dict) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.get(f"{TASKS_URL}/{task_id}", headers=member_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_viewer(client: AsyncClient, member_headers: dict, viewer_headers: dict) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.get(f"{TASKS_URL}/{task_id}", headers=viewer_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient, member_headers: dict) -> None:
    fake_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    resp = await client.get(f"{TASKS_URL}/{fake_id}", headers=member_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_task_member(client: AsyncClient, member_headers: dict) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.patch(
        f"{TASKS_URL}/{task_id}", json={"title": "Judul Baru"}, headers=member_headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Judul Baru"


@pytest.mark.asyncio
async def test_update_task_status_member(client: AsyncClient, member_headers: dict) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.patch(
        f"{TASKS_URL}/{task_id}/status",
        json={"status": "in_progress"},
        headers=member_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task_member(client: AsyncClient, member_headers: dict) -> None:
    task_id = await _create_task(client, member_headers)
    resp = await client.delete(f"{TASKS_URL}/{task_id}", headers=member_headers)
    assert resp.status_code == 204


# ─── ADMIN: boleh semua ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tasks_admin(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.get(TASKS_URL, headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_task_admin(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.post(TASKS_URL, json=TASK_BODY, headers=admin_headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_delete_task_admin(client: AsyncClient, admin_headers: dict) -> None:
    task_id = await _create_task(client, admin_headers)
    resp = await client.delete(f"{TASKS_URL}/{task_id}", headers=admin_headers)
    assert resp.status_code == 204


# ─── Token salah tenant ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_wrong_tenant_header(client: AsyncClient, member_headers: dict) -> None:
    bad_headers = {**member_headers, "X-Tenant-ID": "tenant-lain"}
    resp = await client.get(TASKS_URL, headers=bad_headers)
    assert resp.status_code == 403