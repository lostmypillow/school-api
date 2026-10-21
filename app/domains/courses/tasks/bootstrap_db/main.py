import logging
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.exec_sql import exec_sql, init_db, close_db
from app.domains.courses.tasks.bootstrap_db.copy_courses import copy_courses, copy_department_years
from app.domains.courses.tasks.bootstrap_db.copy_departments import copy_departments
from app.domains.courses.tasks.bootstrap_db.copy_employees import copy_employees, copy_course_syllabi
from app.domains.courses.tasks.bootstrap_db.copy_semesters import copy_semesters
from app.domains.courses.lib.parquet_utils import resolve_parquet_dir

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def bootstrap_db() -> dict[str, int] | None:
    """Bootstraps DB by reading Parquet snapshot files directly into Arrow tables and performing bulk copies."""
    try:
        await init_db()
        parquet_dir = await resolve_parquet_dir()
        await exec_sql(command_name="create_tables")
        await exec_sql(command_name="tutors/bootstrap_tutor")

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

        logger.info(msg=f"DB sync complete: {summary}")
        await close_db()
        return summary
    except Exception as e:
        logger.exception("Error occurred", exc_info=e)
    finally:
        await close_db()

class BootstrapSummaryModel(BaseModel):
    """Structured summary schema for DB database bootstrapping counts."""

    model_config = ConfigDict(extra="forbid")

    semesters: int = Field(default=0, description="Total semester records synced")
    departments: int = Field(default=0, description="Total department records synced")
    department_years: int = Field(default=0, description="Total department-year records synced")
    courses: int = Field(default=0, description="Total course records synced")
    courses_syllabi: int = Field(default=0, description="Total course syllabus records synced")
    employees: int = Field(default=0,  description="Total employees synced")
