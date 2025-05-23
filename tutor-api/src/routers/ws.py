from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.models.cardholder import Cardholder
from src.database.exec_sql import exec_sql
from pprint import pformat
import logging
logger = logging.getLogger('uvicorn.error')
router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)
active_connections: dict[str, WebSocket] = {}


async def sync_frontend():
    for connection in active_connections:
        try:
            await active_connections[connection].send_json([
                Cardholder(
                    **await exec_sql(
                        "one",
                        "fetch_role_teacher",
                        card_id=device_info['老師編號']
                    ),
                    **device_info,
                    role="teacher"
                ).model_dump()
                for device_info in await exec_sql(
                    "all",
                    "select_device_db"
                )
            ])
        except Exception as e:
            print(e)


@router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):

    global active_connections
    await websocket.accept()
    active_connections[client_name] = websocket
    await sync_frontend()
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(pformat(data))

    except WebSocketDisconnect:
        logger.warning(f"[WS:{client_name}]\nDisconnected")

    except Exception as e:
        logger.exception(f"[WS:{client_name}]\nUnexpected error: {e}")

    finally:
        active_connections.pop(client_name, None)
        logger.info(f"[WS:{client_name}]\nRemoved from active connections")
