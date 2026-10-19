from anyio import Path
from pyarrow import parquet as pq

from app.core.exec_mssql_async import exec_mssql_async
import logging
from app.domains.tasks.parquet_utils import _prepare_arrow_table
logger = logging.getLogger(__name__)


async def copy_courses(parquet_dir: Path) -> int:
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
    return course_count


async def copy_department_years(parquet_dir: Path) -> int:
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
    return dy_count
