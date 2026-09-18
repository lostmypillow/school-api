import logging
import pathlib
import traceback
from os import path
from typing import Any, Literal

import pyodbc
from sqlalchemy import URL, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings

pyodbc.pooling = False


connection_url = URL.create(
    "mssql+aioodbc",
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    database=settings.DB_NAME,
    query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
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


async def exec_sql(mode: Literal["commit", "one", "all"], command_name: str, **kwargs) -> Any:
    """從檔案執行 SQL 指令, 並根據執行模式回傳結果.

    Parameters
    ----------
    mode : 'commit' | 'one' | 'all'
    要執行的 SQL 操作類型.

    command_name : str
    位於 /sql 資料夾中的 .sql 檔名 (不含副檔名).

    kwargs : dict
    SQL 的參數綁定.

    Returns
    -------
    Any
    根據 mode 而定, 可能為 None、dict 或 dict 的 list.

    
    """
    file_path = path.join(pathlib.Path(__file__).parent.resolve(), "sql", command_name + ".sql")

    if not path.isfile(file_path):
        logging.error(f"[exec_sql:{command_name}] SQL file does not exist at {file_path}")
        raise FileNotFoundError(f"SQL file {command_name}.sql not found")

    try:
        with open(file_path, encoding="utf-8") as file_buffer:
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
    except (SQLAlchemyError, DBAPIError):
        logging.exception(
            f"[exec_sql:{command_name}] DB error in mode={mode}, params={kwargs}:\n{traceback.format_exc()}",
        )
        raise
    except Exception:
        logging.exception(f"[exec_sql:{command_name}] Unexpected error:\n{traceback.format_exc()}")
        raise
