from fastapi import APIRouter
from app.domains.tutor.routers import (
    announcement_router,
    card_router,
    tutors_router,
    update_router,
    ws_router,
)

router = APIRouter(prefix="/tutor")
router.include_router(announcement_router)
router.include_router(card_router)
router.include_router(tutors_router)
router.include_router(update_router)
router.include_router(ws_router)

