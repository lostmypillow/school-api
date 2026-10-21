"""Courses domain API router.

Provides endpoints to query academic course catalogs, including semesters,
departments, department years, and individual course details from MSSQL.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends
from redis_fastapi import cache

from app.core.exec_psql import exec_mssql_async
from .schemas import (
    CourseResponseSchema,
    DepartmentResponseSchema,
    DepartmentYearResponseSchema,
    SemesterResponseSchema,
    CourseSyllabusModel,
)

router = APIRouter(prefix="/courses", tags=["Courses"])
logger = logging.getLogger(__name__)
ERROR_500_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Internal server error occurred while querying MSSQL.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Something went wrong! Error ID: 750bfda3-3f51-47eb-ba28-299e49e59943"
                }
            }
        },
    }
}


@router.get(
    path="/semesters",
    dependencies=[Depends(cache(ttl=60))],
    response_model=list[SemesterResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List all academic semesters",
    description="Retrieve a list of all academic semesters.",
    response_description="A list of semester records including ID, year, semester number and original URL fragment for posterity.",
    responses=ERROR_500_RESPONSE,
)
async def get_semesters() -> list[SemesterResponseSchema]:
    """Fetch all academic semesters from the database.

    Returns:
        list[SemesterResponseSchema]: List of semester objects.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_mssql_async(command_name="courses/select_all_semester")
    except Exception as e:
        error_id = str(uuid.uuid4())
        print(f"[ERROR ID: {error_id}] => {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )


@router.get(
    path="/departments",
    dependencies=[Depends(cache(ttl=60))],
    response_model=list[DepartmentResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List departments by semester",
    description="Retrieve all academic departments associated with a specific semester.",
    response_description="A list of departments matching the specified semester ID.",
    responses=ERROR_500_RESPONSE,
)
async def get_departments(
    semester_id: str = Query(
        ...,
        description="Unique identifier of the semester (e.g., '112_1').",
        examples=["112_1"],
    ),
) -> list[DepartmentResponseSchema]:
    """Fetch all academic departments under a given semester.

    Args:
        semester_id: Unique identifier of the semester (e.g., '112_1').

    Returns:
        list[DepartmentResponseSchema]: List of department objects for the specified semester.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_mssql_async("courses/select_department", semester_id)
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(msg=f"[ERROR ID: {error_id}]", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )


@router.get(
    path="/department_years",
    dependencies=[Depends(cache(ttl=60))],
    response_model=list[DepartmentYearResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List department study years",
    description="Retrieve all academic study years (cohorts) available under a specific department.",
    response_description="A list of department year records matching the specified department ID.",
    responses=ERROR_500_RESPONSE,
)
async def get_years(
    department_id: str = Query(
        ...,
        description="Unique identifier of the department (e.g., '112_1_300').",
        examples=["112_1_300"],
    ),
) -> list[DepartmentYearResponseSchema]:
    """Fetch all academic years under a given department.

    Args:
        department_id: Unique identifier of the department (e.g., '112_1_300').

    Returns:
        list[DepartmentYearResponseSchema]: List of department year objects.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_mssql_async("courses/select_department_year", department_id)
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(msg=f"[ERROR ID: {error_id}]", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )


@router.get(
    path="/courses",
    dependencies=[Depends(cache(ttl=60))],
    response_model=list[CourseResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List courses by department year",
    description="Retrieve all courses for a specific department year, including instructor, schedule, classroom, and other details.",
    response_description="A list of detailed course objects matching the specified department year ID.",
    responses=ERROR_500_RESPONSE,
)
async def get_course(
    department_year_id: str = Query(
        ...,
        description="Unique identifier of the department year (e.g., '112_1_300_101').",
        examples=["112_1_300_101"],
    ),
) -> list[CourseResponseSchema]:
    """Fetch all courses offered for a given department year.

    Args:
        department_year_id: Unique identifier of the department year (e.g., '112_1_300_101').

    Returns:
        list[CourseResponseSchema]: List of courses with complete schedule, instructor, and metadata.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_mssql_async("courses/select_courses", department_year_id)
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(msg=f"[ERROR ID: {error_id}]", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )

@router.get(
    path="/syllabus",
    dependencies=[Depends(cache(ttl=60))],
    response_model=CourseSyllabusModel,
    status_code=status.HTTP_200_OK,
    summary="Get syllabus",
    description="Retrieve syllabus for a specific course.",
    response_description="Syllabus object matching the specified department year ID.",
    responses=ERROR_500_RESPONSE,
)
async def get_syllabus(
    course_id: str = Query(
        ...,
        description="Unique identifier of the course (e.g., '100_1_0078_153447').",
        examples=["100_1_0078_153447"],
    ),
) -> CourseSyllabusModel:
    """Fetch all courses offered for a given department year.

    Args:
        course_id: Unique identifier of the department year (e.g., '112_1_300_101').

    Returns:
        CourseSyllabusModel: Syllabus for course.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        row = await exec_mssql_async("courses/select_syllabus", course_id)
        logger.info(row)
        if len(row) != 1:
            raise ValueError("More than one syllabus for a course ID")
        return row[0]

    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(msg=f"[ERROR ID: {error_id}]", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )
