from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from sqlalchemy import text, URL
import pathlib
from os import path
import logging
from src.config import settings
import pyodbc
from typing import Literal, Any
import traceback

pyodbc.pooling = False


connection_url = URL.create(
    "mssql+aioodbc",
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    database=settings.DB_NAME,
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "TrustServerCertificate": "yes"
    }
)

async_engine = create_async_engine(
    connection_url,
    pool_size=100,
    max_overflow=0,
    pool_pre_ping=True,
)

create_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


async def exec_sql(
    mode: Literal['commit', 'one', 'all'],
    command_name: str,
    **kwargs
) -> Any:
    """Executes SQL command from file and returns result based on mode.

    Parameters
    ----------
    mode : 'commit' | 'one' | 'all'
        Type of SQL operation to perform.

    command_name : str
        The name of the .sql file (without extension) located in /sql.

    kwargs : dict
        SQL parameter bindings.

    Returns
    -------
    Any
        Varies based on mode. Could be None, dict, or list of dicts.
    """
    file_path = path.join(
        pathlib.Path(__file__).parent.resolve(),
        'sql',
        command_name + '.sql'
    )

    if not path.isfile(file_path):
        logging.error(f"[exec_sql:{command_name}] SQL file does not exist at {file_path}")
        raise FileNotFoundError(f"SQL file {command_name}.sql not found")

    try:
        with open(file_path, 'r', encoding="utf-8") as file_buffer:
            sql_command = file_buffer.read()
    except Exception as e:
        logging.exception(f"[exec_sql:{command_name}] Failed to read SQL file: {e}")
        raise

    try:
        async with create_session() as session:
            result = await session.execute(text(sql_command), kwargs)

            if mode == "commit":
                await session.commit()
                return None

            if mode == "one":
                row = result.fetchone()
                return dict(row._mapping) if row else {}

            if mode == "all":
                return [dict(row._mapping) for row in result.fetchall()]
    except (SQLAlchemyError, DBAPIError) as db_err:
        logging.exception(f"[exec_sql:{command_name}] DB error in mode={mode}, params={kwargs}:\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logging.exception(f"[exec_sql:{command_name}] Unexpected error:\n{traceback.format_exc()}")
        raise
