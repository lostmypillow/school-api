from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from httpx import AsyncClient

from src.dependencies import get_http_client
from src.ntut.extract import (
    extract_courses,
    extract_departments,
    extract_semesters,
    extract_years,
)

router = APIRouter(prefix="/ntut", tags=["NTUT"])


@dataclass
class Semester:
    year: str
    sem: str
    link: str


@router.get("/semesters")
async def get_semesters(client: Annotated[AsyncClient, Depends(get_http_client)]):
    return await extract_semesters(client=client)




@router.get("/departments")
async def get_departments(
    year, sem, client: Annotated[AsyncClient, Depends(get_http_client)]
):
    return await extract_departments(client=client, year=year, sem=sem)



@router.get("/years")
async def get_years(
    year, sem, code, client: Annotated[AsyncClient, Depends(get_http_client)]
):
    return await extract_years(client=client, year=year, sem=sem, code=code)




@router.get("/courses")
async def get_course(
    year, sem, code, client: Annotated[AsyncClient, Depends(get_http_client)]
):
    return await extract_courses(client=client, year=year, sem=sem, code=code)


@router.get("/all")
async def get_all_data():
    results = []
    async with httpx.AsyncClient(verify=False) as client:
        semesters = (await extract_semesters(client=client))["list"]
        for semester in semesters:
            year = semester["year"]
            sem = semester["sem"]
            departments = await get_departments(client=client, year=year, sem=sem)
            results.append({"semester": semester, "departments": departments})
    return results
