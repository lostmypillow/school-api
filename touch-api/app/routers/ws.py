from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from app.lib.sync import sync
from pprint import pprint
from app.lib.active_connections import active_connections
ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)

@ws_router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str, bg_tasks: BackgroundTasks):
    global active_connections
    await websocket.accept()
    

    active_connections[client_name] = websocket
    if client_name =='client':
        print("it's client!")
        bg_tasks.add_task(sync)

    try:
        while True:
            data: dict = await websocket.receive_json()
            if "to" in data:
                recipient = data['to']
                if recipient in active_connections:
                    await active_connections[recipient].send_json(data)
            else:
                pprint(data)

    except WebSocketDisconnect:
        print(f"Client {client_name} disconnected.")
    finally:
        # Ensure the connection is removed from the active connections
        active_connections.pop(client_name, None)
        print(f"Removed {client_name} from active connections.")