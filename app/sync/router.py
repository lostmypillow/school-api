from arq import ArqRedis
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, HTTPException
from fastapi import status
from fastapi.requests import Request

router = APIRouter(prefix="/sync", tags=["NTUT to DB sync"])


@router.post("/sqlite")
async def trigger_sync_sqlite(request: Request):
    arq_pool: ArqRedis = request.app.state.arq_redis
    job: Job | None = await arq_pool.enqueue_job("bootstrap_sqlite")
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred. Job not queued",
        )
    return {"status": "Queued", "job_id": job.job_id}


@router.post("/mssql")
async def trigger_sync_mssql(request: Request):
    arq_pool: ArqRedis = request.app.state.arq_redis
    job: Job | None = await arq_pool.enqueue_job("bootstrap_mssql")
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred. Job not queued",
        )
    return {"status": "Queued", "job_id": job.job_id}


@router.get("/status")
async def get_job_status(request: Request, job_id: str):
    arq_pool: ArqRedis = request.app.state.arq_redis

    job = Job(job_id, arq_pool)

    job_status: JobStatus = await job.status()
    if job_status == "not_found":
        return {"job_id": job_id, "status": "not_found", "result": None}

    info = await job.result_info()
    return {
        "job_id": job_id,
        "status": job_status,  # returns:
        "result": info.result if info else None,
    }
