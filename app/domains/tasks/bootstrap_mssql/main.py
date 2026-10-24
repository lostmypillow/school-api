import logging
from typing import Any, TypeVar

import pyarrow.parquet as pq
from pydantic import BaseModel

from app.core.exec_mssql_async import exec_mssql_async
from app.domains.tasks.bootstrap_mssql.schemas import BootstrapSummaryModel
from app.domains.tasks.parquet_utils import resolve_parquet_dir, _prepare_arrow_table

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def bootstrap_mssql(ctx: dict[str, Any] | None = None, *args: Any, **kwargs: Any) -> dict[str, int]:
    """Bootstraps MSSQL by reading Parquet snapshot files directly into Arrow tables and performing bulk copies."""
    if ctx is None:
        ctx = {}
    parquet_dir = await resolve_parquet_dir(ctx=ctx)

    await exec_mssql_async(command_name="create_database")
    await exec_mssql_async(command_name="create_tables")
    await exec_mssql_async(command_name="tutors/bootstrap_tutor", fetch=False)

    logger.info(msg="Semesters -> upsert_semester")
    sem_file = parquet_dir / "semesters.parquet"
    sem_count = 0
    if await sem_file.exists():
        sem_table = pq.read_table(sem_file)
        sem_count = sem_table.num_rows
        if sem_count > 0:
            sem_table = _prepare_arrow_table(sem_table, add_timestamps=True)
            await exec_mssql_async(command_name="courses/upsert_semester", fetch=False)
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "semesters", sem_table, fetch=False)
            logger.info("Bulk copied %d semesters to MSSQL", sem_count)

    logger.info(msg="Departments -> upsert_department")
    dept_file = parquet_dir / "departments.parquet"
    dept_count = 0
    if await dept_file.exists():
        dept_table = pq.read_table(dept_file)
        dept_count = dept_table.num_rows
        if dept_count > 0:
            dept_table = _prepare_arrow_table(dept_table, add_timestamps=True)
            await exec_mssql_async(command_name="courses/upsert_department", fetch=False)
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "departments", dept_table, fetch=False)
            logger.info("Bulk copied %d departments to MSSQL", dept_count)

    logger.info(msg="Department Years -> upsert_department_year")
    dy_file = parquet_dir / "department_years.parquet"
    dy_count = 0
    if await dy_file.exists():
        dy_table = pq.read_table(dy_file)
        dy_count = dy_table.num_rows
        if dy_count > 0:
            dy_table = _prepare_arrow_table(dy_table, add_timestamps=True)
            await exec_mssql_async(command_name="courses/upsert_department_year", fetch=False)
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "department_years", dy_table, fetch=False)
            logger.info("Bulk copied %d department years to MSSQL", dy_count)

    logger.info(msg="Courses -> upsert_course")
    course_file = parquet_dir / "courses.parquet"
    course_count = 0
    if await course_file.exists():
        course_table = pq.read_table(course_file)
        course_count = course_table.num_rows
        if course_count > 0:
            course_table = _prepare_arrow_table(course_table, add_timestamps=True)
            await exec_mssql_async(command_name="courses/upsert_course", fetch=False)
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "courses", course_table, fetch=False)
            logger.info("Bulk copied %d courses to MSSQL", course_count)

    logger.info(msg="Course Syllabi -> upsert_course_syllabi")
    syllabi_file = parquet_dir / "courses_syllabi.parquet"
    if not await syllabi_file.exists() and await (parquet_dir / "course_syllabi.parquet").exists():
        syllabi_file = parquet_dir / "course_syllabi.parquet"
    syllabi_count = 0
    if await syllabi_file.exists():
        syllabi_table = pq.read_table(syllabi_file)
        syllabi_count = syllabi_table.num_rows
        if syllabi_count > 0:
            syllabi_table = _prepare_arrow_table(syllabi_table, add_timestamps=False)
            await exec_mssql_async(command_name="courses/upsert_course_syllabi", fetch=False)
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "course_syllabi", syllabi_table, fetch=False)
            logger.info("Bulk copied %d course syllabi to MSSQL", syllabi_count)

    summary: dict[str, int] = BootstrapSummaryModel(
        semesters=sem_count,
        departments=dept_count,
        department_years=dy_count,
        courses=course_count,
        courses_syllabi=syllabi_count,
    ).model_dump()

    logger.info(msg=f"MSSQL sync complete: {summary}")
    return summary
