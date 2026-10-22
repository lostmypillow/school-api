import logging
from typing import Any
from uuid import uuid4

import nh3
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from app.core.exec_sql import exec_sql
from app.domains.tutor.schemas.announcement import AddAnnouncement, UpdateAnnouncement
from app.domains.tutor.schemas.api_response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/announcements")

TAGS={"p", "strong", "em", "h1", "h2", "h3"}

@router.post("/")
async def add_announcement(announcement: AddAnnouncement) -> APIResponse:
    try:
        logger.info(announcement.model_dump_json(indent=2))
        await exec_sql(
            "insert_announce",
            nh3.clean(announcement.content,tags=TAGS)
        )
        return APIResponse(detail="Adding announcement successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.put("/")
async def update_announcement(announcement: UpdateAnnouncement) -> APIResponse:
    try:
        await exec_sql(
            "update_announce", announcement.id,nh3.clean(announcement.content,tags=TAGS)
        )
        return APIResponse(detail="Updating announcement successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.delete("/{announcement_id}")
async def delete_announcement(announcement_id: int) -> APIResponse:
    try:
        await exec_sql("delete_announce", announcement_id)
        return APIResponse(detail="Deleting announcement successful!!")

    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get("/")
async def get_announcements() -> list[Any] | list[dict[Any, Any]] | str | None:
    try:
        return await exec_sql(command_name="get_announce")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e
