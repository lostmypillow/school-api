from anyio import Path
from pyarrow import parquet as pq

from app.core.exec_sql import exec_sql
import logging
from app.domains.courses.lib.parquet_utils import _prepare_arrow_table
logger = logging.getLogger(__name__)


async def copy_semesters(parquet_dir: Path) -> int:
    logger.info(msg="Semesters -> upsert_semester")
    sem_file = parquet_dir / "semesters.parquet"
    sem_count = 0
    if await sem_file.exists():
        sem_table = pq.read_table(sem_file)
        sem_count = sem_table.num_rows
        if sem_count > 0:
            sem_table = _prepare_arrow_table(sem_table, add_timestamps=True)
            await exec_sql(command_name="courses/upsert_semester")
            await exec_sql("create_tables")
            await exec_sql("bulkcopy_arrow", "semesters", sem_table)
            logger.info("Bulk copied %d semesters to MSSQL", sem_count)
    return sem_count
