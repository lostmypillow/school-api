"""可能與 `src.database.exec_sql` 重複.

聽起來好像我完全不知道這個檔案是怎麼產生的.但事實上我之前確實用這個檔案來放 `exec_sql` 函式, 而且也實際這樣用過. 只是現在, 大多數邏輯都改為從 `src.database` 匯入那個函式了, 所以我也搞不太清楚目前這檔案的定位.


""" # noqa: E501
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Literal

import anyio
import pyodbc
from sqlalchemy import URL, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

logger = logging.getLogger("rich")
pyodbc.pooling = False

# ---------- Database URL and Engine Setup ----------

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

# ---------- Dependency for FastAPI Injection ----------


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with create_session() as session:
        yield session


# ---------- SQL File Executor ----------


async def exec_sql(
    mode: Literal["commit", "one", "all"],
    command_name: str,
    session: AsyncSession,
    **kwargs,  # noqa: ANN003
) -> dict | list[dict] | None:
    file_path = Path.cwd() / "sql" / f"{command_name}.sql"
    logger.info("Reading SQL file from: %s", file_path)

    if not Path(file_path).is_file():
        logger.error("SQL file does not exist at %s", file_path)
        raise FileNotFoundError

    try:
        async with await anyio.open_file(file_path, encoding="utf-8") as file_buffer:
            sql_command = await file_buffer.read()
    except Exception:
        logger.exception("Failed to read SQL file from %s", file_path)

    try:
        result = await session.execute(text(sql_command), kwargs)

        if mode == "commit":
            await session.commit()
            logger.info("Command %s committed", command_name)
            return None

        if mode == "one":
            row = result.fetchone()
            logger.info("Command %s fetched one", command_name)
            return dict(row._mapping) if row else {}  # noqa: SLF001

        if mode == "all":
            logger.info("Command %s fetched all", command_name)
            return [dict(row._mapping) for row in result.fetchall()]  # noqa: SLF001
    except (SQLAlchemyError, DBAPIError):
        logger.exception("SQLAlchemyError or DBAPIError")
        raise
    except Exception:
        logger.exception("Generic Exception")
        raise
