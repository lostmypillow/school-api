import logging

from fastapi import APIRouter

from app.domains.touch.routers import (
    auth,
    seat,
    survey,
    ws,
)

logger = logging.getLogger("__name__")


router = APIRouter(prefix="/touch")


router.include_router(auth.router)

router.include_router(ws.router)

router.include_router(seat.router)

router.include_router(survey.router)
