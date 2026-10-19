from datetime import date
import logging
import time
from typing import Any

import httpx

from app.core.custom_http_client import CustomAsyncClient
from app.domains.courses.schemas import (
    CourseModel,
    DepartmentModel,
    DepartmentYearModel,
    SemesterModel,
    CourseSyllabusModel,
)
from app.domains.tasks.scrape.scrape_courses import (
    scrape_courses,
)
from app.domains.tasks.scrape.scrape_courses_syllabi import scrape_courses_syllabi
from app.domains.tasks.scrape.scrape_department_years import (
    scrape_department_years,
)
from app.domains.tasks.scrape.scrape_departments import scrape_departments
from app.domains.tasks.scrape.sync_employees import sync_employees
from app.domains.tasks.scrape.sync_semesters import (
    sync_semesters,
)
from app.domains.tasks.parquet_utils import (
    read_parquet_models,
    resolve_parquet_dir,
)

logger = logging.getLogger(__name__)


async def scrape_to_parquet(ctx: dict[str, Any] | None = None) -> None:
    """Scrapes NTUT catalog and writes directly to Parquet snapshot files with Pydantic validation."""
    start_time = time.time()
    if ctx is None:
        ctx = {}
    parquet_dir = await resolve_parquet_dir(ctx)
    if "client" not in ctx:
        ctx["client"] = CustomAsyncClient(
            verify=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
            timeout=30.0,
        )

    print(f"Starting catalog scrape (writing directly to Parquet at {parquet_dir})...")

    try:
        dept_models: list[DepartmentModel] = await read_parquet_models(
            parquet_dir / "departments.parquet", DepartmentModel
        )
        dy_models: list[DepartmentYearModel] = await read_parquet_models(
            parquet_dir / "department_years.parquet", DepartmentYearModel
        )
        course_models: list[CourseModel] = await read_parquet_models(
            parquet_dir / "courses.parquet", CourseModel
        )

        course_syllabi_models: list[CourseSyllabusModel] = await read_parquet_models(
            parquet_dir / "courses_syllabi.parquet", CourseSyllabusModel
        )

        existing_dept_semester_ids: set[str] = {m.semester_id for m in dept_models}
        department_with_years: set[str] = {m.department_id for m in dy_models}
        department_years_with_courses: set[str] = {
            m.department_year_id for m in course_models
        }
        courses_with_syllabi: set[str] = {m.course_id for m in course_syllabi_models}

        seen_dep_ids: set[str] = set()
        seen_class_ids: set[str] = set()

        chunk_size = 50
        current_year = date.today().year - 1911
        current_semester = 1 if date.today().month - 6 >= 0 else 2
        current_sem_id = f"{str(current_year)}_{str(current_semester)}"

        semester_list = []
        current_year = date.today().year - 1911
        current_semester = 1 if date.today().month - 6 >= 0 else 2
        semester_list.append(
            {
                "id": f"{str(current_year)}_{str(current_semester)}",
                "year": str(current_year),
                "sem": str(current_semester),
                "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
            }
        )
        while current_year >= 86:
            if current_semester == 2:
                current_semester = 1
            elif current_semester == 1:
                current_semester = 2
                current_year -= 1
            semester_list.append(
                {
                    "id": f"{str(current_year)}_{str(current_semester)}",
                    "year": str(current_year),
                    "sem": str(current_semester),
                    "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
                }
            )
        print(f"Successfully processed semesters data. Length: {len(semester_list)}")

        semester_list = await sync_semesters(
            parquet_dir=parquet_dir, semester_list=semester_list
        )

        # 2. Departments -> Skip semesters already in Parquet
        sems_to_scrape: list[SemesterModel] = [
            sem
            for sem in semester_list
            if sem.id not in existing_dept_semester_ids or sem.id == current_sem_id
        ]

        await scrape_departments(
            ctx=ctx,
            parquet_dir=parquet_dir,
            sems_to_scrape=sems_to_scrape,
            seen_dep_ids=seen_dep_ids,
            chunk_size=chunk_size,
        )

        # 3. Department Years -> Skip departments already in Parquet
        all_departments: list[DepartmentModel] = await read_parquet_models(
            parquet_dir / "departments.parquet", DepartmentModel
        )

        departments_to_scrape: list[DepartmentModel] = [
            d
            for d in all_departments
            if d.id not in department_with_years or d.semester_id == current_sem_id
        ]

        await scrape_department_years(
            ctx=ctx,
            parquet_dir=parquet_dir,
            departments_to_scrape=departments_to_scrape,
            seen_class_ids=seen_class_ids,
            chunk_size=chunk_size,
        )

        # 4. Courses -> Skip department years already in Parquet
        all_dep_years: list[DepartmentYearModel] = await read_parquet_models(
            parquet_dir / "department_years.parquet", DepartmentYearModel
        )

        dep_years_to_scrape: list[DepartmentYearModel] = [
            dy
            for dy in all_dep_years
            if dy.id not in department_years_with_courses
            or dy.id.startswith(current_sem_id)
        ]

        await scrape_courses(
            ctx=ctx,
            parquet_dir=parquet_dir,
            dep_years_to_scrape=dep_years_to_scrape,
            chunk_size=chunk_size,
        )

        all_courses = await read_parquet_models(parquet_dir / "courses.parquet", CourseModel)

        courses_to_scrape: list[CourseModel] = [
            course
            for course in all_courses
            if course.link and course.id not in courses_with_syllabi
        ]

        await scrape_courses_syllabi(
            ctx=ctx,
            parquet_dir=parquet_dir,
            course_to_scrape=courses_to_scrape,
            chunk_size=chunk_size,
        )

        await sync_employees()

        end_time = time.time()
        print(
            {
                "time": f"{round(end_time - start_time, 2)}s",
                "message": "Data scrape and Parquet sync complete!",
            }
        )
        print("NTUT -> Parquet sync completed.")

    except Exception:
        logger.exception("NTUT -> Parquet sync failed")
        raise
    finally:
        client = ctx.get("client")
        if client is not None and hasattr(client, "aclose") and not client.is_closed:
            await client.aclose()
