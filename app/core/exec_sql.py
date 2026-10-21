import logging
from contextlib import asynccontextmanager
from os import getenv
from pathlib import Path
from typing import Any, Optional
import asyncio
import adbc_driver_postgresql.dbapi as adbc_dbapi
import asyncpg
from asyncpg import Pool, create_pool, Connection
from asyncpg.pool import PoolAcquireContext
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.tables.base import Base

logger = logging.getLogger(__name__)

CONNECT_RETRY_ERRORS = frozenset(
    {
        "Timeout expired",
        "Connection timeout expired",
        "Client unable to establish connection",
        "Communication link failure",
        "Connection failure during transaction",
    }
)
_pool: Optional[Pool] = None
DSN = f"postgresql://postgres:{getenv('DB_PWD','')}@{getenv('DB_HOST','')}:5432/student_db"
async def init_db():
    global _pool
    if _pool is None:
        _pool = await create_pool(dsn=DSN, min_size=5, max_size=10) # type: ignore[misc]


async def close_db():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_connection() -> PoolAcquireContext:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return _pool.acquire()

@asynccontextmanager
async def start_transaction():
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    async with _pool.acquire() as conn:
        conn: Connection
        async with conn.transaction():
            yield conn



async def bulkcopy_arrow(table_name: str, arrow_table):
    def _adbc_ingest():
        with adbc_dbapi.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.adbc_ingest(table_name, arrow_table, mode="append")
            conn.commit()
    await asyncio.to_thread(_adbc_ingest)


async def exec_sql(
    command_name: str, *params: Any
) -> list[Any] | list[dict[Any, Any]] | str | None:
    """Executes a named SQL script file from app/core/sql/"""
    global _pool

    if command_name == "create_tables":
        ddl_statements = []
        for table in Base.metadata.sorted_tables:
            create_sql = str(CreateTable(table, if_not_exists=True).compile(dialect=postgresql.dialect())).strip()
            ddl_statements.append(f"{create_sql};")
        sql_command = "\n\n".join(ddl_statements)

    elif command_name == "bulkcopy_arrow":
        return await bulkcopy_arrow(params[0], params[1])

    else:
        base_sql_dir = Path(__file__).parent / "sql"
        file_path = base_sql_dir / f"{command_name}.sql"
        if not file_path.exists():
            matched = list[Path](base_sql_dir.rglob(f"{command_name}.sql"))
            if matched:
                file_path = matched[0]

        try:
            sql_command = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error("sql_not_found: SQL file does not exist at %s", file_path)
            raise
        except OSError as exc:
            logger.error(
                "sql_cant_read: Failed to read SQL file %s: %s", file_path, exc
            )
            raise
    try:
        async with start_transaction() as conn:
            if command_name == "create_tables" or command_name == "tutors/bootstrap_tutor":
                await conn.execute(sql_command)
                return None
            records = await conn.fetch(sql_command, *params)
            return [dict(record) for record in records]
    except asyncpg.exceptions.PostgresError as exc:
        logger.exception("DB_execution_error: Error running %s: %s", command_name, exc)
        raise