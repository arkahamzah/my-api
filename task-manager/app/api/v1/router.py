from fastapi import APIRouter
from app.api.v1.endpoints import tasks, tenants

router = APIRouter()
router.include_router(tasks.router)
router.include_router(tenants.router)

from app.api.v1.endpoints.auth import router as auth_router
router.include_router(auth_router)
