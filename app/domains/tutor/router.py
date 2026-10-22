import re

from fastapi import APIRouter
from app.domains.tutor.routers import (
    announcement_router,
    card_router,
    ws_router
)
import logging
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from asyncpg import UniqueViolationError
from app.core.exec_sql import exec_sql
from app.domains.tutor.schemas.api_response import APIResponse
from app.domains.tutor.schemas.tutor import TutorCreate, TutorResponse, TutorUpdate


router = APIRouter(prefix="/tutor",tags=["Tutors"])



logger = logging.getLogger(__name__)


@router.post(
    path="/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tutor",
    description="Create a tutor record in the employees table.",
)
async def create_tutor(tutor: TutorCreate) -> APIResponse:
    try:
        await exec_sql(
            "create_tutor",
            tutor.id,
            tutor.name,
            tutor.card_id,
            tutor.college,
            tutor.new_college,
            tutor.department,
            tutor.email,
        )
        return APIResponse(detail="Creating tutor successful!!")
    except UniqueViolationError as exc:
        err_msg = str(exc)
        constraint_match = re.search(pattern=r'unique constraint "([^"]+)"', string=err_msg)
        constraint_name = constraint_match.group(1) if constraint_match else None
        detail_match = re.search(pattern=r"Key \((.*?)\)=\((.*?)\) already exists", string=err_msg)
        if detail_match:
            conflicting_column = detail_match.group(1)
            conflicting_value = detail_match.group(2)
            error_message = f"Cannot create employee. Employee with {conflicting_column} of {conflicting_value} already exists!"
        else:
            error_message = "Cannot create employee due to unknown conflict"
            logger.error(f"Unique violation on constraint: {constraint_name}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_message)
    except Exception as e:
        logger.exception(msg="Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get(
    path="/page/{page}",
    response_model=list[TutorResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tutors",
    description="Retrieve all tutor records from the employees table.",
)
async def get_all_tutors(page: int) -> list[Any] | list[dict[Any, Any]] | str | None:
    try:
        page_size = 10
        return await exec_sql("get_all_tutors", page_size, (page - 1) * page_size)
    except Exception as e:
        logger.exception(msg="Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get(
    path="/{tutor_id}",
    response_model=TutorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tutor by ID",
    description="Retrieve a single tutor record by employee ID.",
)
async def get_tutor(tutor_id: str) -> Any:
    try:
        records = await exec_sql("get_tutor", tutor_id)
        if not records or not isinstance(records, list) or len(records) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor with id '{tutor_id}' not found",
            )
        return records[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e

@router.put(
    path="/",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tutor",
    description="Update an existing tutor record using the ID in payload.",
)
async def update_tutor(tutor: TutorUpdate) -> APIResponse:
    if not tutor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutor ID is required",
        )
    try:
        await exec_sql(
            "update_tutor",
            tutor.id,
            tutor.name,
            tutor.card_id,
            tutor.college,
            tutor.new_college,
            tutor.department,
            tutor.email,
        )
        return APIResponse(detail="Updating tutor successful!!")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.delete(
    path="/",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete tutor",
    description="Delete a tutor record by ID.",
)
async def delete_tutor(tutor: TutorUpdate) -> APIResponse:
    if not tutor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutor ID is required",
        )
    try:
        await exec_sql("delete_tutor", tutor.id)
        return APIResponse(detail="Deleting tutor successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


router.include_router(announcement_router)
router.include_router(card_router)
router.include_router(ws_router)