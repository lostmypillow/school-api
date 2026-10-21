import pyarrow as pa
from anyio import Path
from pyarrow import compute as pc
from pyarrow import parquet as pq

from app.core.exec_sql import exec_sql
import logging
from app.domains.courses.lib.parquet_utils import _prepare_arrow_table
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
            for col_name in ("credits", "students_enrolled", "students_dropped"):
                if col_name in course_table.column_names:
                    idx = course_table.schema.get_field_index(col_name)
                    try:
                        col = pc.cast(course_table[col_name], pa.int32())
                    except Exception:
                        col = pc.cast(pc.cast(course_table[col_name], pa.float64()), pa.int32(), safe=False)
                    course_table = course_table.set_column(idx, col_name, col)
            await exec_sql(command_name="courses/upsert_course")
            await exec_sql("create_tables")
            await exec_sql("bulkcopy_arrow", "courses", course_table)
            logger.info("Bulk copied %d courses to DB", course_count)
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
            await exec_sql(command_name="courses/upsert_department_year")
            await exec_sql("create_tables")
            await exec_sql("bulkcopy_arrow", "department_years", dy_table)
            logger.info("Bulk copied %d department years to DB", dy_count)
    return dy_count
