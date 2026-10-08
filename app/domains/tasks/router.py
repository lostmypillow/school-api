from fastapi import APIRouter, HTTPException, status
from fastapi.requests import Request
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from app.domains.tasks.jobs import bootstrap_mssql_task, scrape_to_parquet_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _get_queue(request: Request) -> Queue:
    if hasattr(request.app.state, "rq_queue") and request.app.state.rq_queue is not None:
        return request.app.state.rq_queue
    redis_conn = getattr(request.app.state, "redis", None) or getattr(request.app.state, "rq_redis", None)
    return Queue(connection=redis_conn)


def _get_redis(request: Request):
    return getattr(request.app.state, "redis", None) or getattr(request.app.state, "rq_redis", None)


@router.post("/scrape-to-parquet")
async def trigger_scrape_to_parquet(request: Request):
    queue = _get_queue(request)
    try:
        job: Job | None = queue.enqueue(scrape_to_parquet_task)
    except Exception:
        job = None
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred. Job not queued",
        )
    return {"status": "Queued", "job_id": getattr(job, "id", getattr(job, "job_id", None))}


@router.post("/bootstrap-mssql")
async def trigger_bootstrap_mssql(request: Request):
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
    return {"status": "Queued", "job_id": getattr(job, "id", getattr(job, "job_id", None))}


@router.get("/status")
async def get_job_status(request: Request, job_id: str):
    redis_conn = _get_redis(request)
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError:
        return {"job_id": job_id, "status": "not_found", "result": None}

    job_status = job.get_status() if callable(getattr(job, "get_status", None)) else getattr(job, "status", None)
    if job_status == "not_found" or job_status is None:
        return {"job_id": job_id, "status": "not_found", "result": None}

    return {
        "job_id": job_id,
        "status": job_status,
        "result": getattr(job, "result", None),
    }
