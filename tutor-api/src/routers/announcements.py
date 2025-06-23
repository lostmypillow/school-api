import logging
from uuid import uuid4

from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.database.exec_sql import exec_sql
from src.models.announcement import AddAnnouncement, UpdateAnnouncement
from src.models.api_response import APIResponse

logger = logging.getLogger("rich")
router = APIRouter(prefix="/announcements", tags=["Announcments"])


@router.post("/")
async def add_announcement(announcement: AddAnnouncement):
    try:
        print(announcement.model_dump())
        await exec_sql("commit", "insert_announce", content=announcement.content)
        return APIResponse(detail="Adding announcement successful!!")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}")


@router.put("/")
async def update_announcement(announcement: UpdateAnnouncement):
    try:
        await exec_sql(
            "commit",
            "update_announce",
            id=announcement.id,
            content=announcement.content,
        )
        return APIResponse(detail="Updating announcement successful!!")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}")


@router.delete("/{id}")
async def delete_announcement(id: int):
    try:
        await exec_sql("commit", "delete_announce", id=id)
        return APIResponse(detail="Deleting announcement successful!!")

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}")


@router.get("/")
async def get_announcements():
    try:
        return await exec_sql("all", "get_announce")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Error {uuid4()!s}")
