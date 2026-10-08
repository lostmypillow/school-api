import asyncio
import logging
from os import getenv
from pathlib import Path
import time
from typing import Any

import mssql_python
from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateTable

from app.core.models import Base

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


def connect_with_retry(
    conn_str: str, max_attempts: int = 3, login_timeout_s: int = 5
) -> mssql_python.Connection:
    """Open a connection using mssql-python, retrying transient failures with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            conn = mssql_python.connect(
                conn_str,
                attrs_before={mssql_python.SQL_ATTR_LOGIN_TIMEOUT: login_timeout_s},
            )
            return conn
        except mssql_python.OperationalError as exc:
            err_msg = getattr(exc, "driver_error", str(exc))
            if err_msg not in CONNECT_RETRY_ERRORS or attempt == max_attempts:
                logger.error(
                    "connect failed on attempt %d/%d: %s",
                    attempt,
                    max_attempts,
                    err_msg,
                )
                raise
            delay = 2 ** (attempt - 1)
            logger.warning(
                "connect attempt %d/%d hit transient error %r; retrying in %ds",
                attempt,
                max_attempts,
                err_msg,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError("unreachable: connection retry loop exited without return or raise")


def exec_mssql(
    command_name: str,
    *params: Any,
    fetch: bool = True,
    batch_params: list[tuple] | list[list] | None = None,
) -> list[Any] | None:
    """Executes a named SQL script file from app/core/sql/ using mssql-python."""
    conn_str: str
    if command_name == "create_tables":
        dialect = mssql.dialect()
        ddl_statements = []

        for table in Base.metadata.sorted_tables:
            create_sql = str(CreateTable(table).compile(dialect=dialect)).strip()
            wrapped_sql = f"""IF OBJECT_ID(N'{table.name}', N'U') IS NULL
    BEGIN
    {create_sql}
    END;"""
            ddl_statements.append(wrapped_sql)

        sql_command = "\n\n".join(ddl_statements)
        conn_str = getenv("BOOTSTRAP_URL", "")
    else:
        file_path = Path(__file__).resolve().parent / "sql" / f"{command_name}.sql"
        conn_str = getenv("DB_URL", "")

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
    if conn_str == "":
        raise ValueError("conn_str is empty check env")

    try:
        with connect_with_retry(conn_str) as conn:
            with conn.cursor() as cursor:
                if batch_params is not None:
                    cursor.executemany(sql_command, batch_params)
                    result = None
                else:
                    cursor.execute(sql_command, *params)
                    try:
                        result = cursor.fetchall() if fetch else None
                    except mssql_python.Error:
                        result = None
            conn.commit()
            return result
    except mssql_python.Error as exc:
        logger.error("mssql_execution_error: Error running %s: %s", command_name, exc)
        raise


async def exec_mssql_async(
    command_name: str,
    *params: Any,
    fetch: bool = True,
    batch_params: list[tuple] | list[list] | None = None,
) -> list[Any] | None:
    """Asynchronously executes a named SQL script in a worker thread."""
    return await asyncio.to_thread(
        exec_mssql, command_name, *params, fetch=fetch, batch_params=batch_params
    )
