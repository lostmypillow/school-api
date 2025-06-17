from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..logger import logger
from src.lib.get_class_with_seats import get_class_with_seats
from pprint import pformat
client_connections: dict[str, WebSocket] = {}
debug_connections: dict[str, WebSocket] = {}
ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)


async def send_updates():
    if client_connections:
        for client_name, con in list(client_connections.items()):
            try:
                await con.send_json({
                    "action": "update class",
                    "message": await get_class_with_seats()
                })
            except Exception as e:
                logger.warning(
                    f"[WS:{client_name}] Failed to send update: {e}")
                client_connections.pop(client_name, None)


@ws_router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    """
    WebSocket connection endpoint for real-time control interface.

    Parameters
    ----------
    websocket : WebSocket
        The WebSocket connection object.
    client_name : str
        Unique identifier for the client.

    Description
    -----------
    Accepts real-time control or sync messages from clients.
    Maintains a persistent connection and updates all connected clients 
    with class and seat data when `send_updates()` is called.
    """
    global client_connections
    await websocket.accept()
    client_connections[client_name] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # if debug_connections:
            #     for c_name, con in list(debug_connections.items()):
            #         await con.send_text(data)

            logger.info(pformat(data))
            if data == 'debug':
                for c_name, con in list(client_connections.items()):
                    await con.send_text('debug_toggle')
                    await con.send_text(', '.join(client_connections))

    except WebSocketDisconnect:
        logger.warning(f"[WS:{client_name}]\nDisconnected")

    except Exception as e:
        logger.exception(f"[WS:{client_name}]\nUnexpected error: {e}")

    finally:
        client_connections.pop(client_name, None)
        logger.info(f"[WS:{client_name}]\nRemoved from active connections")

