import logging
from fastapi.responses import orjson
from app.core.exec_mssql_async import exec_mssql_async
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.lib.connection_manager import manager

logger = logging.getLogger(__name__)


async def sync_frontend() -> None:
    try:
        teachers = [
            Cardholder(
                **((await exec_mssql_async("fetch_role_teacher", device_info["teacher_id"])) or [{}])[0],
                **device_info,
                role="teacher",
            ).model_dump()
            for device_info in await exec_mssql_async(command_name="select_device_db")
        ]

        # Fetch and serialize announcements
        # pyrefly: ignore [missing-attribute]
        announce = orjson.dumps(await exec_mssql_async("get_announce") or []).decode()

    except Exception as e:
        logger.exception("Error preparing frontend data", exc_info=e)
        return

    await manager.broadcast({
        "teachers": teachers,
        "announce": announce,
    })
