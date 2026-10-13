import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.internal.talk import repositories as talk_repositories

# Alias legacy module path app.features.talk.repositories for talk service
sys.modules["app.features.talk.repositories"] = talk_repositories

from app.domains.internal.talk.repositories import (  # noqa: E402
    NextcloudRepository,
)
from app.domains.internal.talk.schemas import (  # noqa: E402
    SendMessageRequest,
    SendMessageResponse,
)
from app.domains.internal.talk.services import NextcloudService  # noqa: E402


def test_talk_schemas():
    """Test SendMessageRequest and SendMessageResponse schemas."""
    req = SendMessageRequest(
        sender="alice",
        recipient="bob",
        message="Hello World",
        password="secretpassword",
    )
    assert req.sender == "alice"
    assert req.recipient == "bob"

    resp = SendMessageResponse(
        success=True,
        detail="Message sent",
        result={"id": 101},
    )
    assert resp.success is True
    assert resp.result == {"id": 101}


@pytest.mark.asyncio
async def test_nextcloud_service_send_message_existing_room():
    """Test send_message reuses existing room when found."""
    mock_repo = MagicMock(spec=NextcloudRepository)
    mock_repo.return_existing_rooms = AsyncMock(
        return_value=[
            {"displayName": "Direct chat with bob", "token": "room_token_123"}
        ]
    )
    mock_repo.send_message = AsyncMock(return_value={"status": "sent"})

    service = NextcloudService(repo=mock_repo)
    result = await service.send_message(
        sender="alice",
        recipient="bob",
        message="Hi Bob",
        password="pwd",
    )

    assert result["success"] is True
    assert result["detail"] == "Message sent as alice"
    assert result["result"] == {"status": "sent"}
    mock_repo.create_room.assert_not_called()
    mock_repo.send_message.assert_awaited_once_with(
        auth=("alice", "pwd"),
        message="Hi Bob",
        token="room_token_123",
    )


@pytest.mark.asyncio
async def test_nextcloud_service_send_message_create_room():
    """Test send_message creates a new room if none exists."""
    mock_repo = MagicMock(spec=NextcloudRepository)
    mock_repo.return_existing_rooms = AsyncMock(return_value=[])
    mock_repo.create_room = AsyncMock(return_value={"token": "new_room_token"})
    mock_repo.send_message = AsyncMock(return_value={"status": "sent"})

    service = NextcloudService(repo=mock_repo)
    result = await service.send_message(
        sender="alice",
        recipient="charlie",
        message="Hello Charlie",
        password="pwd",
    )

    assert result["success"] is True
    mock_repo.create_room.assert_awaited_once_with(
        auth=("alice", "pwd"),
        recipient="charlie",
    )
    mock_repo.send_message.assert_awaited_once_with(
        auth=("alice", "pwd"),
        message="Hello Charlie",
        token="new_room_token",
    )


@pytest.mark.asyncio
async def test_nextcloud_service_send_message_error_handling():
    """Test send_message handles exceptions and returns success=False."""
    mock_repo = MagicMock(spec=NextcloudRepository)
    mock_repo.return_existing_rooms = AsyncMock(
        side_effect=RuntimeError("Nextcloud API unreachable")
    )

    service = NextcloudService(repo=mock_repo)
    result = await service.send_message(
        sender="alice",
        recipient="bob",
        message="Hello",
        password="pwd",
    )

    assert result["success"] is False
    assert "Nextcloud API unreachable" in result["detail"]
