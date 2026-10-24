import logging
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasting for the Tutor domain."""

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[client_name] = websocket

    def disconnect(self, client_name: str) -> None:
        self.active_connections.pop(client_name, None)

    async def broadcast(self, data: dict) -> None:
        for client_name, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(data)
            except WebSocketDisconnect:
                self.disconnect(client_name)
            except Exception as e:
                logger.exception("Failed to send WebSocket message to %s", client_name, exc_info=e)


manager = ConnectionManager()
