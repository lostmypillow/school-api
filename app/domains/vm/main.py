from fastapi import APIRouter

from .routers import legacy, vv


router = APIRouter(prefix="/vm")

router.include_router(legacy.router, prefix="/legacy")
router.include_router(vv.router, prefix="/vv")

