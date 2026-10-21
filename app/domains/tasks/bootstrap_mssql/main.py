import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.exec_psql import exec_mssql_async, init_db, close_db
from app.domains.tasks.bootstrap_mssql.copy_courses import copy_courses, copy_department_years
from app.domains.tasks.bootstrap_mssql.copy_departments import copy_departments
from app.domains.tasks.bootstrap_mssql.copy_employees import copy_employees, copy_course_syllabi
from app.domains.tasks.bootstrap_mssql.copy_semesters import copy_semesters
from app.domains.tasks.parquet_utils import resolve_parquet_dir

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def bootstrap_mssql(ctx: dict[str, Any] | None = None) -> dict[str, int]:
    """Bootstraps MSSQL by reading Parquet snapshot files directly into Arrow tables and performing bulk copies."""
    try:
        await init_db()
        if ctx is None:
            ctx = {}
        parquet_dir = await resolve_parquet_dir(ctx=ctx)
        await exec_mssql_async(command_name="create_tables")
        await exec_mssql_async(command_name="tutors/bootstrap_tutor")

        sem_count = await copy_semesters(parquet_dir)
        dept_count = await copy_departments(parquet_dir)
        department_year_count = await copy_department_years(parquet_dir)
        course_count = await copy_courses(parquet_dir)
        syllabi_count = await copy_course_syllabi(parquet_dir)
        employee_count = await copy_employees(parquet_dir)

        summary: dict[str, int] = BootstrapSummaryModel(
            semesters=sem_count,
            departments=dept_count,
            department_years=department_year_count,
            courses=course_count,
            courses_syllabi=syllabi_count,
            employees=employee_count
        ).model_dump()

        logger.info(msg=f"MSSQL sync complete: {summary}")
        await close_db()
        return summary
    except Exception as e:
        logger.exception("Error occurred", exc_info=e)
    finally:
        await close_db()

class BootstrapSummaryModel(BaseModel):
    """Structured summary schema for MSSQL database bootstrapping counts."""

    model_config = ConfigDict(extra="forbid")

    semesters: int = Field(default=0, description="Total semester records synced")
    departments: int = Field(default=0, description="Total department records synced")
    department_years: int = Field(default=0, description="Total department-year records synced")
    courses: int = Field(default=0, description="Total course records synced")
    courses_syllabi: int = Field(default=0, description="Total course syllabus records synced")
    employees: int = Field(default=0,  description="Total employees synced")
