from anyio import Path
from pyarrow import parquet as pq

from app.core.exec_sql import exec_sql
import logging
from app.domains.courses.lib.parquet_utils import _prepare_arrow_table
logger = logging.getLogger(__name__)


async def copy_departments(parquet_dir: Path) -> int:
    logger.info(msg="Departments -> upsert_department")
    dept_file = parquet_dir / "departments.parquet"
    dept_count = 0
    if await dept_file.exists():
        dept_table = pq.read_table(dept_file)
        dept_count = dept_table.num_rows
        if dept_count > 0:
            dept_table = _prepare_arrow_table(dept_table, add_timestamps=True)
            await exec_sql(command_name="courses/upsert_department")
            await exec_sql("create_tables")
            await exec_sql("bulkcopy_arrow", "departments", dept_table)
            logger.info("Bulk copied %d departments to MSSQL", dept_count)
    return dept_count
