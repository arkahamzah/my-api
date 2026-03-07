"""
Locust load testing untuk Task Manager API.
Jalankan: locust -f locustfile.py --host=http://localhost:8000
"""
import random
import string

from locust import HttpUser, between, task

TENANT_UUID = "11111111-1111-1111-1111-111111111111"


def random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


class TaskManagerUser(HttpUser):
    wait_time = between(1, 3)
    token: str | None = None

    def on_start(self):
        """Register lalu login untuk dapat token."""
        username = random_string()
        email = f"{username}@loadtest.com"
        password = "LoadTest123!"
        headers = {"X-Tenant-ID": TENANT_UUID}

        self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": username, "password": password},
            headers=headers,
        )

        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers=headers,
        )

        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": TENANT_UUID,
        }

    @task(3)
    def list_tasks(self):
        if not self.token:
            return
        self.client.get(
            f"/api/v1/tenants/{TENANT_UUID}/tasks",
            headers=self._headers(),
        )

    @task(2)
    def create_task(self):
        if not self.token:
            return
        self.client.post(
            f"/api/v1/tenants/{TENANT_UUID}/tasks",
            headers=self._headers(),
            json={
                "title": f"Task {random_string()}",
                "description": "Load test task",
                "priority": random.choice(["low", "medium", "high"]),
            },
        )

    @task(1)
    def health_check(self):
        self.client.get("/health")
