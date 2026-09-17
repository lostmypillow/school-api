import logging
from uuid import uuid4

import nh3
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.database.exec_sql import exec_sql
from src.models.announcement import AddAnnouncement, Announcement, UpdateAnnouncement
from src.models.api_response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/announcements", tags=["Announcments"])

def sanitize_html(raw_html: str) -> str:
    return nh3.clean(raw_html,tags={"p", "strong", "em", "h1", "h2", "h3"})


@router.post("/")
async def add_announcement(announcement: AddAnnouncement) -> APIResponse:
    try:
        logger.info(announcement.model_dump_json(indent=2))
        await exec_sql(
            "commit",
            "insert_announce",
            content=sanitize_html(announcement.content),
            )
        return APIResponse(detail="Adding announcement successful!!")
    except Exception as e:
        logger.exception()
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}") from e


@router.put("/")
async def update_announcement(announcement: UpdateAnnouncement) -> APIResponse:
    try:
        await exec_sql(
            "commit",
            "update_announce",
            id=announcement.id,
            content=sanitize_html(announcement.content),
        )
        return APIResponse(detail="Updating announcement successful!!")
    except Exception as e:
        logger.exception()
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}") from e


@router.delete("/{announcment_id}")
async def delete_announcement(announcment_id: int) -> APIResponse:
    try:
        await exec_sql("commit", "delete_announce", id=announcment_id)
        return APIResponse(detail="Deleting announcement successful!!")

    except Exception as e:
        logger.exception()
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}") from e


@router.get("/")
async def get_announcements() -> list[Announcement]:
    try:
        return await exec_sql("all", "get_announce")
    except Exception as e:
        logger.exception()
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}") from e
