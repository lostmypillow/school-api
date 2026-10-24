import logging
from typing import Any

import orjson
from app.core.exec_sql import exec_sql
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.lib.connection_manager import manager

logger = logging.getLogger(__name__)


async def get_teacher_cardholder(
    device_info: dict[str, Any],
) -> dict[str, Any]:
    teacher_id = device_info.get("teacher_id")
    sql_res = await exec_sql("fetch_role_teacher", teacher_id)

    teacher_data: dict[str, Any] = {}
    if (
        isinstance(sql_res, list)
        and len(sql_res) > 0
        and isinstance(sql_res[0], dict)
    ):
        teacher_data = sql_res[0]

    base_data = {
        **teacher_data,
        **device_info,
    }

    cardholder = Cardholder(
        **base_data,
        role="teacher",
    )
    return cardholder.model_dump()



async def sync_frontend() -> None:
    teachers: list[dict[str, Any]] = []

    try:
        raw_devices = await exec_sql(command_name="select_device_db")

        if isinstance(raw_devices, list):
            devices: list[dict[str, Any]] = [
                dev for dev in raw_devices if isinstance(dev, dict)
            ]

            teachers = [
                await get_teacher_cardholder(device_info)
                for device_info in devices
            ]

        # pyrefly: ignore [missing-attribute]
        announce = orjson.dumps(
            await exec_sql("get_announce") or []
        ).decode()

    except Exception as e:
        logger.exception("Error preparing frontend data", exc_info=e)
        return

    await manager.broadcast({
        "teachers": teachers,
        "announce": announce,
    })