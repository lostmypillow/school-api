# app/database/exec_sql.py
import logging
from pathlib import Path
from typing import Literal

import anyio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def exec_sql(
    mode: Literal["commit", "one", "all"],
    command_name: str,
    session: AsyncSession,
    **args,
):
    file_path = Path(__file__).resolve().parent / "sql" / f"{command_name}.sql"

    if not Path(file_path).is_file():
        logger.info(f"sql_not_found: SQL file does not exist at {file_path}")
        raise FileNotFoundError

    # noinspection PyBroadException
    try:
        async with await anyio.open_file(file_path, encoding="utf-8") as file_buffer:
            sql_command = await file_buffer.read()
    except Exception:  # noqa: BLE001
        logger.info(f"sql_cant_read: Failed to read SQL file from {file_path}")

    try:
        result = await session.execute(text(sql_command), args)

        if mode == "commit":
            await session.commit()
            return None

        if mode == "one":
            result = result.fetchone()
            return await result.mappings().first() or {}

        if mode == "all":
            return result.mappings().all()
        logger.info("sql_known_error: SQLAlchemyError or DBAPIError")
        raise
    except Exception:
        logger.info("sql_unknown_error: Generic Exception")
        raise