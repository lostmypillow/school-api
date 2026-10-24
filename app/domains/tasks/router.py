from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.requests import Request
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.domains.tasks.definitions import bootstrap_mssql_task, scrape_to_parquet_task
from app.domains.tasks.schemas import TaskQueueResponse, JobStatusResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _get_queue(request: Request) -> Queue:
    if hasattr(request.app.state, "rq_queue") and request.app.state.rq_queue is not None:
        return request.app.state.rq_queue
    redis_conn = getattr(request.app.state, "redis", None) or getattr(request.app.state, "rq_redis", None)
    return Queue(connection=redis_conn)


def _get_redis(request: Request) -> Any | None:
    return getattr(request.app.state, "redis", None) or getattr(request.app.state, "rq_redis", None)


@router.post(
    "/scrape-to-parquet",
    response_model=TaskQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Enqueue NTUT catalog scraping task",
    description="Submits a background task to scrape the NTUT catalog and append snapshots to Parquet files.",
)
async def trigger_scrape_to_parquet(
    request: Request
) -> TaskQueueResponse:
    queue = _get_queue(request)
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
    "/bootstrap-mssql",
    response_model=TaskQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Enqueue MSSQL database bootstrap task",
    description="Submits a background task to bootstrap MSSQL tables and upsert records from Parquet snapshots.",
)
async def trigger_bootstrap_mssql(request: Request) -> TaskQueueResponse:
    queue = _get_queue(request)
    try:
        job: Job | None = queue.enqueue(bootstrap_mssql_task)
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
    "/status",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get background task execution status",
    description="Checks the current status and result of a queued or completed RQ task by job ID.",
)
async def get_job_status(
    request: Request,
    job_id: str = Query(..., description="Unique RQ job identifier"),
) -> JobStatusResponse:
    redis_conn = _get_redis(request)
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
