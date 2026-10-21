from anyio import Path
from pyarrow import parquet as pq

from app.core.exec_psql import exec_mssql_async
import logging
from app.domains.tasks.parquet_utils import _prepare_arrow_table
logger = logging.getLogger(__name__)


async def copy_employees(parquet_dir: Path) -> int:
    logger.info(msg="Employees -> upsert_employees")
    employee_file = parquet_dir / "employees.parquet"
    if not await employee_file.exists() and await (parquet_dir / "employees.parquet").exists():
        employee_file = parquet_dir / "employees.parquet"
    employee_count = 0
    if await employee_file.exists():
        employee_table = pq.read_table(employee_file)
        employee_count = employee_table.num_rows
        if employee_count > 0:
            employee_table = _prepare_arrow_table(employee_table, add_timestamps=False)
            await exec_mssql_async(command_name="courses/upsert_employees")
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "employees", employee_table)
            logger.info("Bulk copied %d employees to MSSQL", employee_count)
    return employee_count


async def copy_course_syllabi(parquet_dir: Path) -> int:
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
            await exec_mssql_async(command_name="courses/upsert_course_syllabi")
            await exec_mssql_async("create_tables")
            await exec_mssql_async("bulkcopy_arrow", "course_syllabi", syllabi_table)
            logger.info("Bulk copied %d course syllabi to MSSQL", syllabi_count)
    return syllabi_count
