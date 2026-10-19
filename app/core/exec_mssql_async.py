import asyncio
import logging
from os import getenv
from pathlib import Path
import time
from typing import Any

import mssql_python
from sqlalchemy.dialects import mssql
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
                print(f"DEBUG: err_msg={err_msg!r}")
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
) -> list[Any]:
    """Executes a named SQL script file from app/core/sql/ using mssql-python."""

    conn_str = getenv("DB_URL", "")
    if command_name == "create_database":
        conn_str = getenv("BOOTSTRAP_URL", "")
        sql_command = "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'student_db') CREATE DATABASE student_db;"
    elif command_name == "create_tables":
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
    elif command_name == "bulkcopy_arrow":
        sql_command = ""
    else:
        base_sql_dir = Path(__file__).parent / "sql"
        file_path = base_sql_dir / f"{command_name}.sql"
        if not file_path.exists():
            matched = list(base_sql_dir.rglob(f"{command_name}.sql"))
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
    if conn_str == "":
        raise ValueError("conn_str is empty check env")

    try:
        with connect_with_retry(conn_str) as conn:
            if command_name == 'create_database':
                conn.autocommit = True
            with conn.cursor() as cursor:
                if command_name == "bulkcopy_arrow":
                    cursor.bulkcopy_arrow(params[0], params[1])
                    result = []
                elif batch_params is not None:
                    cursor.executemany(sql_command, batch_params)
                    result: list[Any] = []
                else:
                    cursor.execute(sql_command, *params)
                    try:
                        if fetch and cursor.description:
                            col_names = [col[0] for col in cursor.description]
                            rows = cursor.fetchall()
                            result = [dict(zip(col_names, row)) for row in rows] if rows else []
                        elif fetch:
                            rows = cursor.fetchall()
                            result = list(rows) if rows else []
                        else:
                            result = []
                    except mssql_python.Error:
                        result = []
            conn.commit()
            return result if result is not None else []
    except mssql_python.Error as exc:
        logger.error("mssql_execution_error: Error running %s: %s", command_name, exc)
        raise


async def exec_mssql_async(
    command_name: str,
    *params: Any,
    fetch: bool = True,
    batch_params: list[tuple] | list[list] | None = None,
) -> list[Any]:
    """Asynchronously executes a named SQL script in a worker thread."""
    return await asyncio.to_thread(
        exec_mssql, command_name, *params, fetch=fetch, batch_params=batch_params
    )


# Aliases
execute_mssql = exec_mssql
mssql_async = exec_mssql_async
execute_mssql_async = exec_mssql_async
