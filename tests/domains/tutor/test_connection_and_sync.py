"""Unit tests for ConnectionManager and sync_frontend in Tutor domain."""
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect
import pytest

from app.domains.tutor.lib.connection_manager import ConnectionManager
from app.domains.tutor.lib.sync_frontend import sync_frontend


@pytest.mark.asyncio
async def test_connection_manager_connect_and_disconnect():
    """Test connection manager adds and removes active websocket connections."""
    cm = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)

    await cm.connect("client_1", mock_ws)
    mock_ws.accept.assert_awaited_once()
    assert "client_1" in cm.active_connections

    cm.disconnect("client_1")
    assert "client_1" not in cm.active_connections


@pytest.mark.asyncio
async def test_connection_manager_broadcast_and_auto_cleanup():
    """Test broadcast delivers json to connected clients and cleans up disconnected ones."""
    cm = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)
    ws2.send_json.side_effect = WebSocketDisconnect()

    cm.active_connections["client_ok"] = ws1
    cm.active_connections["client_dead"] = ws2

    payload = {"message": "hello"}
    await cm.broadcast(payload)

    ws1.send_json.assert_awaited_once_with(payload)
    # ws2 raised WebSocketDisconnect, so it should be removed
    assert "client_ok" in cm.active_connections
    assert "client_dead" not in cm.active_connections


@pytest.mark.asyncio
async def test_sync_frontend_payload_shape():
    """Test sync_frontend fetches device and teacher data and broadcasts exact payload shape."""
    devices = [{"device_id": 1, "teacher_id": "T01"}]
    teacher_row = [{"id": "T01", "name": "李老師", "college": "電機系"}]
    announcements = [{"id": 1, "content": "公告1"}]

    async def mock_exec(command_name, *args, **kwargs):
        if command_name == "select_device_db":
            return devices
        if command_name == "fetch_role_teacher":
            return teacher_row
        if command_name == "get_announce":
            return announcements
        return []

    with (
        patch("app.domains.tutor.lib.sync_frontend.exec_mssql_async", side_effect=mock_exec),
        patch("app.domains.tutor.lib.sync_frontend.manager.broadcast", new_callable=AsyncMock) as mock_broadcast,
    ):
        await sync_frontend()

    mock_broadcast.assert_awaited_once()
    broadcast_data = mock_broadcast.call_args[0][0]

    assert "teachers" in broadcast_data
    assert "announce" in broadcast_data

    # Verify teachers list
    teachers = broadcast_data["teachers"]
    assert isinstance(teachers, list)
    assert len(teachers) == 1
    t = teachers[0]
    assert t["card_id"] == "T01"
    assert t["name"] == "李老師"
    assert t["role"] == "teacher"
    assert t["device_id"] == 1

    # Verify announce JSON string
    assert isinstance(broadcast_data["announce"], str)
    assert "公告1" in broadcast_data["announce"]
