from fastapi import APIRouter, Request, HTTPException
from fastapi.params import Depends
import uuid
from redis_fastapi import cache
from sqlalchemy import select

from app.db.models import Semester, Department, DepartmentYear, Course

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/semesters", dependencies=[Depends(cache(ttl=60))])
async def get_semesters(request: Request):
    try:
        result: list[Semester] = []
        async with request.app.state.db.get_session() as session:
            result = (await session.scalars(select(Semester))).all()
        return result
    except Exception as e:
        error_id = str(uuid.uuid4())
        print(f"[ERROR ID: {error_id}] => {e}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong! Error ID: {error_id}"
        )


@router.get("/departments", dependencies=[Depends(cache(ttl=60))])
async def get_departments(request: Request, semester_id: str):
    try:
        result: list[Department] = []
        async with request.app.state.db.get_session() as session:
            result = (
                await session.scalars(
                    select(Department).where(Department.semester_id == semester_id)
                )
            ).all()
        return result
    except Exception as e:
        error_id = str(uuid.uuid4())
        print(f"[ERROR ID: {error_id}] => {e}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong! Error ID: {error_id}"
        )


@router.get("/department_years", dependencies=[Depends(cache(ttl=60))])
async def get_years(request: Request, department_id):
    try:
        result: list[DepartmentYear] = []
        async with request.app.state.db.get_session() as session:
            result = (
                await session.scalars(
                    select(DepartmentYear).where(
                        DepartmentYear.department_id == department_id
                    )
                )
            ).all()

        return result
    except Exception as e:
        error_id = str(uuid.uuid4())
        print(f"[ERROR ID: {error_id}] => {e}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong! Error ID: {error_id}"
        )


@router.get("/courses", dependencies=[Depends(cache(ttl=60))])
async def get_course(request: Request, department_year_id: str):
    try:
        result: list[Course] = []
        async with request.app.state.db.get_session() as session:
            result = (
                await session.scalars(
                    select(Course).where(
                        Course.department_year_id == department_year_id
                    )
                )
            ).all()
        return result
    except Exception as e:
        error_id = str(uuid.uuid4())
        print(f"[ERROR ID: {error_id}] => {e}")
        raise HTTPException(
            status_code=500, detail=f"Something went wrong! Error ID: {error_id}"
        )
