import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


from app.domains.tutor.lib.connection_manager import manager
from app.domains.tutor.lib.sync_frontend import sync_frontend

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/tutor/ws",
    tags=["Websocket / Control"],
)


@router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str) -> None:
    await manager.connect(client_name, websocket)
    await sync_frontend()
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(data)
            if data == "sync":
                await sync_frontend()

    except WebSocketDisconnect:
        logger.exception("Websocket Disconnected for client: %s", client_name)

    except Exception as e:
        logger.exception("Unexpected error for client: %s", client_name, exc_info=e)

    finally:
        manager.disconnect(client_name)
        logger.info("Client %s removed from active connections", client_name)
