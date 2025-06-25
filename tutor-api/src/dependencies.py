# dependencies.py

import logging
from collections.abc import AsyncGenerator
from os import getcwd, path
from typing import Any, Literal
from pathlib import Path
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
    **kwargs,
) -> Any:
    """Executes SQL command from file and returns result based on mode."""
    file_path = path.join(getcwd(), "sql", f"{command_name}.sql")
    logger.info(f"Reading SQL file from: {file_path}")

    if not Path(file_path).is_file():
        logger.error("SQL file does not exist at %s",file_path)
        raise FileNotFoundError

    try:
        with open(file_path, encoding="utf-8") as file_buffer:
            sql_command = file_buffer.read()
    except Exception as e:
        logger.exception(f"Failed to read SQL file from {file_path}")
        raise e

    try:
        result = await session.execute(text(sql_command), kwargs)

        if mode == "commit":
            await session.commit()
            logger.info(f"Command {command_name} committed")
            return None

        if mode == "one":
            row = result.fetchone()
            logger.info(f"Command {command_name} fetched one")
            return dict(row._mapping) if row else {}

        if mode == "all":
            logger.info(f"Command {command_name} fetched all")
            return [dict(row._mapping) for row in result.fetchall()]
    except (SQLAlchemyError, DBAPIError):
        logger.exception(
            f"""
            SQLAlchemyError or DBAPIError
            Command name: {command_name},
            DB error in mode={mode},
            params={kwargs}
        """,
        )
        raise
    except Exception:
        logger.exception(
            f"""
            Exception
            Command name: {command_name},
            DB error in mode={mode},
            params={kwargs}
        """,
        )
        raise
