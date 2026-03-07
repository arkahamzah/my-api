"""
Background tasks untuk audit logging.
Dijalankan async setelah response dikirim ke client.
"""
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


async def log_task_created(task_id: UUID, tenant_id: UUID, created_by: UUID, title: str) -> None:
    """Simulasi audit log - di production bisa kirim ke DB / message queue."""
    logger.info(
        "AUDIT | task_created | task_id=%s tenant_id=%s by=%s title='%s' at=%s",
        task_id, tenant_id, created_by, title, datetime.utcnow().isoformat(),
    )


async def log_task_status_changed(task_id: UUID, tenant_id: UUID, old_status: str, new_status: str) -> None:
    logger.info(
        "AUDIT | task_status_changed | task_id=%s tenant_id=%s %s→%s at=%s",
        task_id, tenant_id, old_status, new_status, datetime.utcnow().isoformat(),
    )


async def log_tenant_created(tenant_id: UUID, slug: str, plan: str) -> None:
    logger.info(
        "AUDIT | tenant_created | tenant_id=%s slug=%s plan=%s at=%s",
        tenant_id, slug, plan, datetime.utcnow().isoformat(),
    )
