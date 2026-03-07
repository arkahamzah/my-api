import pytest
from uuid import uuid4
from app.application.commands.task_commands import CreateTaskCommand, UpdateTaskCommand, DeleteTaskCommand, UpdateTaskStatusCommand
from app.application.queries.task_queries import GetTaskByIdQuery, ListTasksQuery
from app.application.use_cases.task_use_cases import TaskUseCases
from app.core.exceptions import ForbiddenError, NotFoundError
from tests.helpers.in_memory_repos import InMemoryTaskRepo

@pytest.fixture
def use_cases(): return TaskUseCases(InMemoryTaskRepo())

@pytest.fixture
def tenant_id(): return uuid4()

@pytest.fixture
def user_id(): return uuid4()

async def make_task(uc, tenant_id, user_id, **kw):
    d = dict(tenant_id=tenant_id, created_by=user_id, title="Test Task"); d.update(kw)
    return await uc.create(CreateTaskCommand(**d))

class TestCreateTask:
    @pytest.mark.asyncio
    async def test_basic(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        assert t.title == "Test Task" and t.status == "todo" and t.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_with_tags(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id, tags=("backend","api"))
        assert "backend" in t.tags

    @pytest.mark.asyncio
    async def test_unique_ids(self, use_cases, tenant_id, user_id):
        t1 = await make_task(use_cases, tenant_id, user_id)
        t2 = await make_task(use_cases, tenant_id, user_id)
        assert t1.id != t2.id

class TestUpdateTask:
    @pytest.mark.asyncio
    async def test_update_title(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        u = await use_cases.update(UpdateTaskCommand(id=t.id, tenant_id=tenant_id, title="New"))
        assert u.title == "New"

    @pytest.mark.asyncio
    async def test_partial_preserves_fields(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id, priority="high")
        u = await use_cases.update(UpdateTaskCommand(id=t.id, tenant_id=tenant_id, title="X"))
        assert u.priority == "high"

    @pytest.mark.asyncio
    async def test_wrong_tenant_raises_forbidden(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        with pytest.raises(ForbiddenError):
            await use_cases.update(UpdateTaskCommand(id=t.id, tenant_id=uuid4(), title="Hack"))

    @pytest.mark.asyncio
    async def test_nonexistent_raises_notfound(self, use_cases, tenant_id):
        with pytest.raises(NotFoundError):
            await use_cases.update(UpdateTaskCommand(id=uuid4(), tenant_id=tenant_id, title="X"))

class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_todo_to_in_progress(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        u = await use_cases.update_status(UpdateTaskStatusCommand(id=t.id, tenant_id=tenant_id, status="in_progress"))
        assert u.status == "in_progress"

    @pytest.mark.asyncio
    async def test_to_done(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        u = await use_cases.update_status(UpdateTaskStatusCommand(id=t.id, tenant_id=tenant_id, status="done"))
        assert u.status == "done"

    @pytest.mark.asyncio
    async def test_wrong_tenant_raises_forbidden(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        with pytest.raises(ForbiddenError):
            await use_cases.update_status(UpdateTaskStatusCommand(id=t.id, tenant_id=uuid4(), status="done"))

class TestDeleteTask:
    @pytest.mark.asyncio
    async def test_delete_existing(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        assert await use_cases.delete(DeleteTaskCommand(id=t.id, tenant_id=tenant_id)) is True

    @pytest.mark.asyncio
    async def test_deleted_not_found(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        await use_cases.delete(DeleteTaskCommand(id=t.id, tenant_id=tenant_id))
        with pytest.raises(NotFoundError):
            await use_cases.get_by_id(GetTaskByIdQuery(id=t.id, tenant_id=tenant_id))

    @pytest.mark.asyncio
    async def test_nonexistent_raises_notfound(self, use_cases, tenant_id):
        with pytest.raises(NotFoundError):
            await use_cases.delete(DeleteTaskCommand(id=uuid4(), tenant_id=tenant_id))

class TestListTasks:
    @pytest.mark.asyncio
    async def test_list_by_tenant(self, use_cases, tenant_id, user_id):
        for i in range(3): await make_task(use_cases, tenant_id, user_id, title=f"T{i}")
        assert len(await use_cases.list_tasks(ListTasksQuery(tenant_id=tenant_id))) == 3

    @pytest.mark.asyncio
    async def test_filter_by_status(self, use_cases, tenant_id, user_id):
        t = await make_task(use_cases, tenant_id, user_id)
        await make_task(use_cases, tenant_id, user_id)
        await use_cases.update_status(UpdateTaskStatusCommand(id=t.id, tenant_id=tenant_id, status="done"))
        done = await use_cases.list_tasks(ListTasksQuery(tenant_id=tenant_id, status="done"))
        assert len(done) == 1 and done[0].status == "done"

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, use_cases, user_id):
        t1, t2 = uuid4(), uuid4()
        await make_task(use_cases, t1, user_id)
        await make_task(use_cases, t2, user_id)
        result = await use_cases.list_tasks(ListTasksQuery(tenant_id=t1))
        assert len(result) == 1 and result[0].tenant_id == t1

    @pytest.mark.asyncio
    async def test_pagination(self, use_cases, tenant_id, user_id):
        for i in range(5): await make_task(use_cases, tenant_id, user_id, title=f"T{i}")
        p1 = await use_cases.list_tasks(ListTasksQuery(tenant_id=tenant_id, skip=0, limit=3))
        p2 = await use_cases.list_tasks(ListTasksQuery(tenant_id=tenant_id, skip=3, limit=3))
        assert len(p1) == 3 and len(p2) == 2
