import logging
from pprint import pformat

import orjson
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.database.exec_sql import exec_sql
from src.models.cardholder import Cardholder

logger = logging.getLogger("rich")
router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)
active_connections: dict[str, WebSocket] = {}


async def sync_frontend() -> None:
    try:
        # Fetch and prepare teacher data once
        teachers = [
            Cardholder(
                **await exec_sql("one", "fetch_role_teacher", card_id=device_info["老師編號"]),
                **device_info,
                role="teacher",
            ).model_dump()
            for device_info in await exec_sql("all", "select_device_db")
        ]

        # Fetch and serialize announcements
        announce = orjson.dumps(await exec_sql("all", "get_announce")).decode()

    except Exception:
        logger.exception("Error preparing frontend data")
        return

    for websocket in active_connections.values():
        try:
            await websocket.send_json({
                "teachers": teachers,
                "announce": announce,
            })
        except WebSocketDisconnect:
            logger.exception("WebSocket Disconnected")
        except Exception:
            logger.exception("Unexpected error")




@router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str) -> None:
    await websocket.accept()
    active_connections[client_name] = websocket
    await sync_frontend()
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(pformat(data))
            if data == "sync":
                await sync_frontend()

    except WebSocketDisconnect:
        logger.exception("Websocket Disconnected for client: %s", client_name)

    except Exception:
        logger.exception("Unexpected error  for client: %s", client_name)

    finally:
        active_connections.pop(client_name, None)
        logger.info("Client %s removed from active connections", client_name)
