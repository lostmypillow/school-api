"""SQL 執行器.

.. todo::
    請參考 `src.database` 以取得重構建議.


"""

import logging
import pathlib
import traceback
from os import path
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import declarative_base

from src.database.sessionmanager import sessionmanager

Base = declarative_base()
logger = logging.getLogger("rich")


async def exec_sql(
    mode: Literal["commit", "one", "all"],
    command_name: str,
    **kwargs,
) -> Any:
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
    file_path = path.join(
        pathlib.Path(__file__).parent.resolve(),
        "sql",
        command_name + ".sql",
    )

    if not path.isfile(file_path):
        logger.error(f"[exec_sql:{command_name}] SQL file does not exist at {file_path}")
        raise FileNotFoundError(f"SQL file {command_name}.sql not found")

    try:
        with open(file_path, encoding="utf-8") as file_buffer:
            sql_command = file_buffer.read()
    except Exception as e:
        logger.exception(f"[exec_sql:{command_name}] Failed to read SQL file: {e}")
        raise

    try:
        async with sessionmanager.session() as session:
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
        logger.exception(
            f"[exec_sql:{command_name}] DB error in mode={mode}, params={kwargs}:\n{traceback.format_exc()}",
        )
        raise
    except Exception:
        logger.exception(f"[exec_sql:{command_name}] Unexpected error:\n{traceback.format_exc()}")
        raise
