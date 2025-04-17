from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.lib.active_connections import active_connections
from src.lib.custom_logger import logger

ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)

client_online = False


@ws_router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    global active_connections
    global client_online
    await websocket.accept()
    active_connections[client_name] = websocket

    
    

    try:
        
        while True:
            data = await websocket.receive_json()
            logger.info(data)


    except WebSocketDisconnect:
        print(f"Client {client_name} disconnected.")


    finally:
        # Ensure the connection is removed from the active connections
        active_connections.pop(client_name, None)
        
        print(f"Removed {client_name} from active connections.")
