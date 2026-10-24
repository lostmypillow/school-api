import logging
from uuid import uuid4

import nh3
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from app.core.exec_mssql_async import exec_mssql_async
from app.domains.tutor.schemas.announcement import AddAnnouncement, Announcement, UpdateAnnouncement
from app.domains.tutor.schemas.api_response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/announcements", tags=["Announcements"])

def sanitize_html(raw_html: str) -> str:
    return nh3.clean(raw_html,tags={"p", "strong", "em", "h1", "h2", "h3"})


@router.post("/")
async def add_announcement(announcement: AddAnnouncement) -> APIResponse:
    try:
        logger.info(announcement.model_dump_json(indent=2))
        await exec_mssql_async(
            "insert_announce",
            sanitize_html(announcement.content),
            fetch=False
            )
        return APIResponse(detail="Adding announcement successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.put("/")
async def update_announcement(announcement: UpdateAnnouncement) -> APIResponse:
    try:
        await exec_mssql_async(
            "update_announce", announcement.id,sanitize_html(announcement.content), fetch=False
        )
        return APIResponse(detail="Updating announcement successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.delete("/{announcement_id}")
async def delete_announcement(announcement_id: int) -> APIResponse:
    try:
        await exec_mssql_async("delete_announce", announcement_id, fetch=False)
        return APIResponse(detail="Deleting announcement successful!!")

    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get("/")
async def get_announcements() -> list[Announcement] | None:
    try:
        return await exec_mssql_async(command_name="get_announce")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e
