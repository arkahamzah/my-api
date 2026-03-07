import time
from uuid import uuid4
import pytest
from app.domain.entities.user import User
from app.domain.value_objects.role import Permission, Role

def make_user(role=Role.MEMBER):
    return User.create(email="t@t.com", username="u", hashed_password="h",
                       tenant_id="t1", role=role)

class TestPermissions:
    def test_admin_has_all(self):
        admin = make_user(Role.ADMIN)
        for p in Permission:
            assert admin.has_permission(p)

    def test_member_task_crud(self):
        m = make_user(Role.MEMBER)
        for p in [Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_DELETE]:
            assert m.has_permission(p)

    def test_member_no_admin_panel(self):
        assert not make_user(Role.MEMBER).has_permission(Permission.ADMIN_PANEL)

    def test_member_no_read_all(self):
        assert not make_user(Role.MEMBER).has_permission(Permission.TASK_READ_ALL)

    def test_viewer_read_only(self):
        v = make_user(Role.VIEWER)
        assert v.has_permission(Permission.TASK_READ)
        assert not v.has_permission(Permission.TASK_CREATE)

class TestCanManageTask:
    def test_owner_can_manage_own(self):
        u = make_user()
        assert u.can_manage_task(u.id)

    def test_member_cannot_manage_others(self):
        assert not make_user(Role.MEMBER).can_manage_task(uuid4())

    def test_admin_can_manage_any(self):
        assert make_user(Role.ADMIN).can_manage_task(uuid4())

class TestLifecycle:
    def test_deactivate_activate(self):
        u = make_user()
        u.deactivate(); assert not u.is_active
        u.activate(); assert u.is_active

    def test_change_role_updates_timestamp(self):
        u = make_user()
        before = u.updated_at
        time.sleep(0.01)
        u.change_role(Role.VIEWER)
        assert u.updated_at >= before
