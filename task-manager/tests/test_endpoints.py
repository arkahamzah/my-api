"""
Endpoint tests - Phase 2 (updated).
Menggunakan conftest.py override, tanpa DB.
"""
import pytest
from uuid import uuid4

TENANT_PAYLOAD = {
    "name": "Acme Corp",
    "slug": "acme-corp",
    "owner_email": "owner@acme.com",
    "plan": "free",
    "max_members": 5,
}

# ── Tenant Endpoints ──────────────────────────────────────────────────────────
class TestTenantEndpoints:
    def test_create_tenant(self, client):
        r = client.post("/api/v1/tenants", json=TENANT_PAYLOAD)
        assert r.status_code == 201
        assert r.json()["slug"] == "acme-corp"

    def test_create_duplicate_slug_returns_409(self, client):
        client.post("/api/v1/tenants", json=TENANT_PAYLOAD)
        r = client.post("/api/v1/tenants", json=TENANT_PAYLOAD)
        assert r.status_code == 409

    def test_get_tenant_by_id(self, client):
        created = client.post("/api/v1/tenants", json=TENANT_PAYLOAD).json()
        r = client.get(f"/api/v1/tenants/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_nonexistent_tenant_returns_404(self, client):
        r = client.get(f"/api/v1/tenants/{uuid4()}")
        assert r.status_code == 404

    def test_list_tenants(self, client):
        client.post("/api/v1/tenants", json=TENANT_PAYLOAD)
        r = client.get("/api/v1/tenants")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_update_tenant(self, client):
        created = client.post("/api/v1/tenants", json=TENANT_PAYLOAD).json()
        r = client.patch(f"/api/v1/tenants/{created['id']}", json={"name": "New Name"})
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_delete_tenant(self, client):
        created = client.post("/api/v1/tenants", json=TENANT_PAYLOAD).json()
        r = client.delete(f"/api/v1/tenants/{created['id']}")
        assert r.status_code == 204


# ── Task Endpoints ────────────────────────────────────────────────────────────
class TestTaskEndpoints:
    @pytest.fixture
    def tenant_id(self, client):
        r = client.post("/api/v1/tenants", json=TENANT_PAYLOAD)
        return r.json()["id"]

    def task_payload(self, **kw):
        d = {"title": "Test Task", "priority": "medium"}
        d.update(kw)
        return d

    def test_create_task(self, client, tenant_id):
        r = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload())
        assert r.status_code == 201
        assert r.json()["title"] == "Test Task"

    def test_list_tasks(self, client, tenant_id):
        client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload())
        client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload(title="Task Two"))
        r = client.get(f"/api/v1/tenants/{tenant_id}/tasks")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_task_by_id(self, client, tenant_id):
        created = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload()).json()
        r = client.get(f"/api/v1/tenants/{tenant_id}/tasks/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_nonexistent_task_returns_404(self, client, tenant_id):
        r = client.get(f"/api/v1/tenants/{tenant_id}/tasks/{uuid4()}")
        assert r.status_code == 404

    def test_update_task(self, client, tenant_id):
        created = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload()).json()
        r = client.patch(f"/api/v1/tenants/{tenant_id}/tasks/{created['id']}", json={"title": "Updated"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    def test_update_task_status(self, client, tenant_id):
        created = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload()).json()
        r = client.patch(f"/api/v1/tenants/{tenant_id}/tasks/{created['id']}/status", json={"status": "in_progress"})
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    def test_delete_task(self, client, tenant_id):
        created = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload()).json()
        r = client.delete(f"/api/v1/tenants/{tenant_id}/tasks/{created['id']}")
        assert r.status_code == 204

    def test_filter_tasks_by_status(self, client, tenant_id):
        created = client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload()).json()
        client.post(f"/api/v1/tenants/{tenant_id}/tasks", json=self.task_payload(title="Task Two"))
        client.patch(f"/api/v1/tenants/{tenant_id}/tasks/{created['id']}/status", json={"status": "done"})
        r = client.get(f"/api/v1/tenants/{tenant_id}/tasks?status=done")
        assert r.status_code == 200
        assert all(t["status"] == "done" for t in r.json())

    def test_tenant_isolation(self, client):
        t1 = client.post("/api/v1/tenants", json={**TENANT_PAYLOAD, "slug": "tenant-1"}).json()["id"]
        t2 = client.post("/api/v1/tenants", json={**TENANT_PAYLOAD, "slug": "tenant-2"}).json()["id"]
        client.post(f"/api/v1/tenants/{t1}/tasks", json=self.task_payload())
        r = client.get(f"/api/v1/tenants/{t2}/tasks")
        assert r.json() == []
