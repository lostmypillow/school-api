import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.core.exec_sql import exec_sql
from app.domains.tutor.schemas.api_response import APIResponse
from app.domains.tutor.schemas.tutor import TutorCreate, TutorResponse, TutorUpdate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tutors"])


@router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tutor",
    description="Create a tutor record in the employees table.",
)
@router.post(
    "/tutors",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
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
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get(
    "/",
    response_model=list[TutorResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tutors",
    description="Retrieve all tutor records from the employees table.",
)
@router.get(
    "/tutors",
    response_model=list[TutorResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_all_tutors() -> list[Any] | list[dict[Any, Any]] | str | None:
    try:
        return await exec_sql("get_all_tutors")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.get(
    "/{tutor_id}",
    response_model=TutorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tutor by ID",
    description="Retrieve a single tutor record by employee ID.",
)
@router.get(
    "/tutors/{tutor_id}",
    response_model=TutorResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
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
    "/{tutor_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tutor by ID",
    description="Update an existing tutor record by ID.",
)
@router.put(
    "/tutors/{tutor_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_tutor_by_id(tutor_id: str, tutor: TutorUpdate) -> APIResponse:
    try:
        await exec_sql(
            "update_tutor",
            tutor_id,
            tutor.name,
            tutor.card_id,
            tutor.college,
            tutor.new_college,
            tutor.department,
            tutor.email,
        )
        return APIResponse(detail="Updating tutor successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e


@router.put(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tutor",
    description="Update an existing tutor record using the ID in payload.",
)
async def update_tutor(tutor: TutorUpdate) -> APIResponse:
    if not tutor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutor ID is required in body when updating via root path",
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
    "/{tutor_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete tutor",
    description="Delete a tutor record by employee ID.",
)
@router.delete(
    "/tutors/{tutor_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_tutor(tutor_id: str) -> APIResponse:
    try:
        await exec_sql("delete_tutor", tutor_id)
        return APIResponse(detail="Deleting tutor successful!!")
    except Exception as e:
        logger.exception("Internal Server Error", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Error {uuid4()!s}") from e
