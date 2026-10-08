import itertools
import logging
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.core.db import exec_mssql_async

logger = logging.getLogger(__name__)


def _read_parquet_records(file_path: Path) -> list[dict[str, Any]]:
    """Reads a Parquet file and returns a list of row dictionaries."""
    if not file_path.exists():
        return []
    return pq.read_table(file_path).to_pylist()


async def bootstrap_mssql(ctx: dict | None = None, *args, **kwargs) -> dict[str, Any]:
    """Bootstraps MSSQL by reading Parquet snapshot files and calling named SQL commands."""
    if ctx is None:
        ctx = {}
    if "parquet_dir" not in ctx:
        DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
        parquet_dir = DATA_DIR / "parquet"
        parquet_dir.mkdir(parents=True, exist_ok=True)
        ctx["parquet_dir"] = parquet_dir
    parquet_dir = Path(ctx["parquet_dir"])

    summary: dict[str, int] = {}
    BATCH_SIZE = 5000

    # 1. Semesters -> upsert_semester
    sem_file = parquet_dir / "semesters.parquet"
    sem_records = _read_parquet_records(sem_file)
    if sem_records:
        sem_tuples = [
            (
                r.get("id"),
                r.get("year"),
                r.get("sem"),
                r.get("link"),
            )
            for r in sem_records
        ]
        await exec_mssql_async("upsert_semester", fetch=False, batch_params=sem_tuples)
        logger.info("Upserted %d semesters to MSSQL", len(sem_tuples))
    summary["semesters"] = len(sem_records)

    # 2. Departments -> upsert_department
    dept_file = parquet_dir / "departments.parquet"
    dept_records = _read_parquet_records(dept_file)
    if dept_records:
        dept_tuples = [
            (
                r.get("id"),
                r.get("semester_id"),
                r.get("year"),
                r.get("sem"),
                r.get("code"),
                r.get("name"),
                r.get("link"),
            )
            for r in dept_records
        ]
        for batch in itertools.batched(dept_tuples, BATCH_SIZE):
            await exec_mssql_async(
                "upsert_department", fetch=False, batch_params=list(batch)
            )
        logger.info("Upserted %d departments to MSSQL", len(dept_tuples))
    summary["departments"] = len(dept_records)

    # 3. Department Years -> upsert_department_year
    dy_file = parquet_dir / "department_years.parquet"
    dy_records = _read_parquet_records(dy_file)
    if dy_records:
        dy_tuples = [
            (
                r.get("id"),
                r.get("department_id"),
                r.get("year"),
                r.get("sem"),
                r.get("code"),
                r.get("name"),
                r.get("link"),
            )
            for r in dy_records
        ]
        for batch in itertools.batched(dy_tuples, BATCH_SIZE):
            await exec_mssql_async(
                "upsert_department_year", fetch=False, batch_params=list(batch)
            )
        logger.info("Upserted %d department years to MSSQL", len(dy_tuples))
    summary["department_years"] = len(dy_records)

    # 4. Courses -> upsert_course
    course_file = parquet_dir / "courses.parquet"
    course_records = _read_parquet_records(course_file)
    if course_records:
        course_tuples = [
            (
                r.get("id"),
                r.get("department_year_id"),
                r.get("year"),
                r.get("sem"),
                r.get("code"),
                r.get("name"),
                r.get("link"),
                r.get("credits"),
                r.get("course_type"),
                r.get("instructor"),
                r.get("sun"),
                r.get("mon"),
                r.get("tue"),
                r.get("wed"),
                r.get("thu"),
                r.get("fri"),
                r.get("sat"),
                r.get("classroom"),
                r.get("students_enrolled"),
                r.get("students_dropped"),
                r.get("language"),
                r.get("notes"),
                r.get("with_class"),
                r.get("experiment"),
                r.get("cross_discipline"),
            )
            for r in course_records
        ]
        for batch in itertools.batched(course_tuples, BATCH_SIZE):
            await exec_mssql_async(
                "upsert_course", fetch=False, batch_params=list(batch)
            )
        logger.info("Upserted %d courses to MSSQL", len(course_tuples))
    summary["courses"] = len(course_records)

    print(f"MSSQL sync complete: {summary}")
    return summary
