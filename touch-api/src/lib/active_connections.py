from fastapi import WebSocket
active_connections: dict[str, WebSocket] = {}