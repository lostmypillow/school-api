from datetime import date
from fastapi import HTTPException
from arq.jobs import Job
from arq.jobs import JobResult
from arq.connections import ArqRedis
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from httpx import AsyncClient

from app.dependencies import get_scrape_client
from app.ntut.extract import (
    extract_courses,
    extract_departments,
    extract_semesters,
    extract_years,
)
from app.tasks import sync_ntut_data

router = APIRouter(prefix="/ntut", tags=["NTUT"])


@dataclass
class Semester:
    year: str
    sem: str
    link: str

@router.get('/test')
async def test():
    array_of_sems = []
    current_year = date.today().year-1911
    current_semester = 2 if date.today().month -6 >= 0 else 1
    array_of_sems.append({"year": current_year, "sem": current_semester})
    while True:
        if current_semester == 2:
            current_semester = 1
        elif current_semester == 1:
            current_semester = 2
            current_year -= 1
        array_of_sems.append({"year": current_year, "sem": current_semester})

        if current_year == 86 and current_semester == 1:
            break


    return array_of_sems

@router.get("/semesters")
async def get_semesters(client: Annotated[AsyncClient, Depends(get_scrape_client)]):
    return await extract_semesters(client=client)


@router.get("/departments")
async def get_departments(
    year, sem, client: Annotated[AsyncClient, Depends(get_scrape_client)]
):
    return await extract_departments(client=client, year=year, sem=sem)


@router.get("/years")
async def get_years(
    year, sem, code, client: Annotated[AsyncClient, Depends(get_scrape_client)]
):
    return await extract_years(client=client, year=year, sem=sem, code=code)


@router.get("/courses")
async def get_course(
    year, sem, code, client: Annotated[AsyncClient, Depends(get_scrape_client)]
):
    return await extract_courses(client=client, year=year, sem=sem, code=code)


@router.post("/sync/start")
async def trigger_sync(request: Request):
    arq_pool: ArqRedis = request.app.state.arq_redis
    job: Job | None = await arq_pool.enqueue_job("sync_ntut_data")
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error occurred. Job not queued")
    return {"status": "Queued in ARQ", "job_id": job.job_id}

@router.get('/sync/status')
async def get_job_status(request:Request, job_id: str):
    arq_pool: ArqRedis = request.app.state.arq_redis

    job = Job(job_id, arq_pool)

    # 3. Check status
    status = await job.status()
    if status == "not_found":
        return {"status": "not_found"}

    info = await job.result_info()
    return {
        "job_id": job_id,
        "status": status,  # returns: queued, in_progress, complete, deferred, not_found
        "result": info.result if info else None,
    }