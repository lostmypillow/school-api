from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from app.lib.sync import sync, list_local, video_queue
from pprint import pprint
from app.lib.active_connections import active_connections
from app.lib.custom_logger import logger
from app.lib.create_cycler import create_cycler
import asyncio
ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket / Control"],
)

@ws_router.websocket("/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    global active_connections
    global video_queue
    await websocket.accept()
    active_connections[client_name] = websocket
    next_video = create_cycler(video_queue)

    try:
        while True:
            # from client: 
            # update: heartbeat every 5s, playing, paused, send_updates every 2s
            # request: next video
            # to client: : 
            data: dict = await websocket.receive_json()

            logger.info(data)
            if data['from'] == 'client':
                if data['action'] == 'request':
                    if data['message'] == 'next video':
                        await active_connections['client'].send_json(
                            {
                                "from": "server",
                                "action": "update video",
                                "message": next_video()
                            }
                        )
                    
            # if "to" in data:
            #     recipient = data['to']
            #     if recipient in active_connections:
            #         await active_connections[recipient].send_json(data)
                

    except WebSocketDisconnect:
        print(f"Client {client_name} disconnected.")
    finally:
        # Ensure the connection is removed from the active connections
        active_connections.pop(client_name, None)
        print(f"Removed {client_name} from active connections.")