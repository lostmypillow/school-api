from .announcements import router as announcement_router
from .card import router as card_router
from .tutors import router as tutors_router
from .update import router as update_router
from .ws import router as ws_router

__all__ = [
    "announcement_router",
    "card_router",
    "tutors_router",
    "update_router",
    "ws_router",
]