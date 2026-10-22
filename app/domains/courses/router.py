"""Courses domain API router.

Provides endpoints to query semesters, departments, department years,
and individual course details from DB.
"""
import logging
import uuid
from typing import Any
from fastapi.requests import Request
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends
from redis_fastapi import cache

from app.core.exec_sql import exec_sql
from .schemas import (
    CourseResponseSchema,
    DepartmentResponseSchema,
    DepartmentYearResponseSchema,
    SemesterResponseSchema,
    CourseSyllabusModel,
)
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.domains.courses.tasks.definitions import bootstrap_db_task, scrape_to_parquet_task
from app.domains.courses.schemas.task_queue import TaskQueueResponse
from app.domains.courses.schemas.job_status import JobStatusResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

logger = logging.getLogger(__name__)

ERROR_500_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Internal server error occurred while querying DB.",
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
async def get_semesters() -> list[Any] | list[dict[Any, Any]] | str | None:
    """Fetch all academic semesters from the database.

    Returns:
        list[SemesterResponseSchema]: List of semester objects.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        row = await exec_sql(command_name="courses/select_all_semester")
        return row
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
) -> list[Any] | list[dict[Any, Any]] | str | None:
    """Fetch all academic departments under a given semester.

    Args:
        semester_id: Unique identifier of the semester (e.g., '112_1').

    Returns:
        list[DepartmentResponseSchema]: List of department objects for the specified semester.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_sql("courses/select_department", semester_id)
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
        default=...,
        description="Unique identifier of the department (e.g., '112_1_300').",
        examples=["112_1_300"],
    ),
) -> list[Any] | list[dict[Any, Any]] | str | None:
    """Fetch all academic years under a given department.

    Args:
        department_id: Unique identifier of the department (e.g., '112_1_300').

    Returns:
        list[DepartmentYearResponseSchema]: List of department year objects.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_sql("courses/select_department_year", department_id)
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
) -> list[Any] | list[dict[Any, Any]] | str | None:
    """Fetch all courses offered for a given department year.

    Args:
        department_year_id: Unique identifier of the department year (e.g., '112_1_300_101').

    Returns:
        list[CourseResponseSchema]: List of courses with complete schedule, instructor, and metadata.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        return await exec_sql("courses/select_courses", department_year_id)
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
        default=...,
        description="Unique identifier of the course (e.g., '100_1_0078_153447').",
        examples=["100_1_0078_153447"],
    ),
) -> str | Any:
    """Fetch all courses offered for a given department year.

    Args:
        course_id: Unique identifier of the department year (e.g., '112_1_300_101').

    Returns:
        CourseSyllabusModel: Syllabus for course.

    Raises:
        HTTPException: 500 Internal Server Error if database query fails.
    """
    try:
        row = await exec_sql("courses/select_syllabus", course_id)
        if not isinstance(row, list) or len(row) != 1:
            raise ValueError("Expected exactly one syllabus for the given course ID")
        return row[0]

    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(msg=f"[ERROR ID: {error_id}]", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong! Error ID: {error_id}",
        )



@router.post(
    path="/scrape",
    response_model=TaskQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Enqueue NTUT catalog scraping task",
    description="Submits a background task to scrape the NTUT catalog and append snapshots to Parquet files.",
)
async def trigger_scrape_to_parquet(
    request: Request
) -> TaskQueueResponse:
    queue = request.app.state.queue
    try:
        job: Job | None = queue.enqueue(scrape_to_parquet_task, job_timeout=3600)
    except Exception:
        job = None
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred. Job not queued",
        )
    return TaskQueueResponse(
        status="Queued",
        job_id=getattr(job, "id", getattr(job, "job_id", None)),
    )


@router.post(
    path="/sync",
    response_model=TaskQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Enqueue DB database bootstrap task",
    description="Submits a background task to bootstrap DB tables and upsert records from Parquet snapshots.",
)
async def trigger_bootstrap_db(request: Request) -> TaskQueueResponse:
    queue = request.app.state.queue
    try:
        job: Job | None = queue.enqueue(bootstrap_db_task)
    except Exception:
        job = None
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred. Job not queued",
        )
    return TaskQueueResponse(
        status="Queued",
        job_id=getattr(job, "id", getattr(job, "job_id", None)),
    )


@router.get(
    path="/status",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get background task execution status",
    description="Checks the current status and result of a queued or completed RQ task by job ID.",
)
async def get_job_status(
    request: Request,
    job_id: str = Query(default=..., description="Unique RQ job identifier"),
) -> JobStatusResponse:
    redis_conn = request.app.state.redis
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError:
        return JobStatusResponse(job_id=job_id, status="not_found", result=None)

    job_status = job.get_status() if callable(getattr(job, "get_status", None)) else getattr(job, "status", None)
    if job_status == "not_found" or job_status is None:
        return JobStatusResponse(job_id=job_id, status="not_found", result=None)

    return JobStatusResponse(
        job_id=job_id,
        status=str(job_status),
        result=getattr(job, "result", None),
    )
