# src/event_manager.py
import asyncio
import json
from typing import List


# List of clients (queues for SSE connections)
clients: List[asyncio.Queue] = []

async def send_event_to_clients(message: dict):
    """Send a message to all connected clients via SSE."""
    for client in clients:
        await client.put(message)

async def event_stream():
    """Streaming data to connected clients (SSE)."""
    while True:
        client = asyncio.Queue()
        clients.append(client)

        try:
            while True:
                message = await client.get()
                yield f"data: {json.dumps(message)}\n\n"
                await asyncio.sleep(1)  # Small sleep to mimic the streaming
        except asyncio.CancelledError:
            clients.remove(client)  # Remove client if it disconnects
