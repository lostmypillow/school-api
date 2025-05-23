from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from src.models.announcement import AddAnnouncement, Announcement
from src.database.exec_sql import exec_sql
import logging
from src.models.api_response import APIResponse
from uuid import uuid4
logger = logging.getLogger('uvicorn.error')
router = APIRouter(
    prefix="/announcements",
    tags=["Announcments"]
)


@router.post('/')
async def add_announcement(announcement: AddAnnouncement):
    try:
        await exec_sql(
            'commit',
            'insert_announce',
            **announcement.model_dump()
        )
        return APIResponse(
            detail="Adding announcement successful!!"
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=404,
            detail=f'Error {str(uuid4())}'
        )


@router.put('/')
async def update_announcement(announcement: Announcement):
    try:
        await exec_sql(
            'commit',
            'update_announce',
            id=announcement.id
        )
        return APIResponse(
            detail="Updating announcement successful!!"
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=404,
            detail=f'Error {str(uuid4())}'
        )


@router.delete('/{id}')
async def delete_announcement(id: int):
    try:
        await exec_sql(
            'commit',
            'delete_announce',
            id=id)
        return APIResponse(
            detail="Deleting announcement successful!!"
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=404,
            detail=f'Error {str(uuid4())}'
        )


@router.get('/')
async def get_announcements():
    try:
        return await exec_sql('all', 'get_announce')
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=404,
            detail=f'Error {str(uuid4())}'
        )
