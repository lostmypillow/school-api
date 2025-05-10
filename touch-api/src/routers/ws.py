from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from src.lib.get_classes_today import get_classes_today
from src.lib.get_class_with_seats import get_class_with_seats
from pprint import pformat
active_connections: dict[str, WebSocket] = {}
ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)


async def send_updates():
    if active_connections:
        for client_name, con in list(active_connections.items()):
            try:
                await con.send_json({
                    "action": "update class",
                    "message": {
                        "classes_today": await get_classes_today(),
                        "class_with_seats": await get_class_with_seats()
                    }
                })
            except Exception as e:
                logging.warning(
                    f"[WS:{client_name}] Failed to send update: {e}")
                active_connections.pop(client_name, None)


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
    global active_connections
    await websocket.accept()
    active_connections[client_name] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            logging.info(pformat(data))

    except WebSocketDisconnect:
        logging.warning(f"[WS:{client_name}]\nDisconnected")

    except Exception as e:
        logging.exception(f"[WS:{client_name}]\nUnexpected error: {e}")

    finally:
        active_connections.pop(client_name, None)
        logging.info(f"[WS:{client_name}]\nRemoved from active connections")

