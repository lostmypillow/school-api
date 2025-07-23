"""WebSocket 端點."""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("rich")
from pprint import pformat

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.lib.get_class_with_seats import get_class_with_seats

client_connections: dict[str, WebSocket] = {}
debug_connections: dict[str, WebSocket] = {}
router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)


async def send_updates() -> None:
    """將更新後的課程資料發送給所有在連線池中的用戶端連線.

    
    """
    if len(list(client_connections.items())) > 0:
        for client_name, con in list(client_connections.items()):
            try:
                await con.send_json({
                    "action": "update class",
                    "message": await get_class_with_seats(),
                })
                logger.info("Sending update...")
            except Exception as e:
                logger.warning(
                    f"[WS:{client_name}] Failed to send update: {e}")



@router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str) -> None:
    """連線後定期將課程資料 (含可補位與即將開課) 發送至前端。中斷連線時會停止排程任務.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket 連線Object。
    client_name : str
        前端用戶的唯一識別碼, 我們在前端使用 `uuid()`: https://www.npmjs.com/package/uuid.
    """
    global client_connections
    await websocket.accept()
    client_connections[client_name] = websocket
    scheduler = AsyncIOScheduler()
    scheduler.start()
    job = scheduler.add_job(
        send_updates,
        "interval",
        seconds=20,
    )
    try:
        while True:
            data = await websocket.receive_text()

            logger.info(pformat(data))
            if data == "update":
                await send_updates()
            if data == "debug":
                for c_name, con in list(client_connections.items()):
                    await con.send_text("debug_toggle")
                    await con.send_text(", ".join(client_connections))

    except WebSocketDisconnect:
        logger.warning(f"[WS:{client_name}]\nDisconnected")

    except Exception as e:
        logger.exception(f"[WS:{client_name}]\nUnexpected error: {e}")

    finally:
        job.remove()
        client_connections.pop(client_name, None)
        logger.info(f"[WS:{client_name}]\nRemoved from active connections")

