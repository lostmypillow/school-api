"""Unit tests for process_card logic in Tutor domain."""
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
import pytest

from app.domains.tutor.process_card import process_card
from app.domains.tutor.schemas.cardholder import Cardholder


@pytest.mark.asyncio
async def test_process_card_device_zero_teacher_success():
    """Test device 0 query with valid teacher returns Cardholder model."""
    teacher = Cardholder(role="teacher", card_id="222222", name="陳老師", device_id=2)

    with patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=teacher)):
        result = await process_card(device_id=0, card_id="222222")

    assert isinstance(result, Cardholder)
    assert result.card_id == "222222"
    assert result.role == "teacher"
    assert result.name == "陳老師"
    assert result.device_id == 2


@pytest.mark.asyncio
async def test_process_card_device_zero_not_found_raises_404():
    """Test device 0 query with unknown cardholder raises 404."""
    with patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value="刷卡失敗: 查無此人")):
        with pytest.raises(HTTPException) as exc_info:
            await process_card(device_id=0, card_id="unknown")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Not found for device 0"


@pytest.mark.asyncio
async def test_process_card_device_non_zero_not_found_returns_error_string():
    """Test device > 0 with unknown cardholder returns error string directly."""
    with patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value="刷卡失敗: 查無此人")):
        result = await process_card(device_id=1, card_id="unknown")

    assert result == "刷卡失敗: 查無此人"


@pytest.mark.asyncio
async def test_process_card_teacher_unassign_same_device():
    """Test teacher swiping on currently assigned device unassigns and returns success."""
    teacher = Cardholder(role="teacher", card_id="T01", name="林老師", device_id=2)

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=teacher)),
        patch("app.domains.tutor.process_card.exec_sql", new_callable=AsyncMock) as mock_exec,
        patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        result = await process_card(device_id=2, card_id="T01")

    assert result == "林老師老師 刷卡成功"
    mock_exec.assert_awaited_once_with("register_update_teacher", None, 2, fetch=False)
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_card_teacher_switch_devices():
    """Test teacher swiping on different device clears old device and assigns new device."""
    teacher = Cardholder(role="teacher", card_id="T01", name="林老師", device_id=1)

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=teacher)),
        patch("app.domains.tutor.process_card.exec_sql", new_callable=AsyncMock) as mock_exec,
        patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        result = await process_card(device_id=2, card_id="T01")

    assert result == "林老師老師 刷卡成功"
    # Old device cleared, new device assigned
    assert mock_exec.await_count == 2
    mock_exec.assert_any_await("register_update_teacher", None, 1, fetch=False)
    mock_exec.assert_any_await("register_update_teacher", "T01", 2, fetch=False)
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_card_teacher_first_device_assignment():
    """Test teacher swiping with device_id=None assigns device and returns success."""
    teacher = Cardholder(role="teacher", card_id="T01", name="林老師", device_id=None)

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=teacher)),
        patch("app.domains.tutor.process_card.exec_sql", new_callable=AsyncMock) as mock_exec,
        patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        result = await process_card(device_id=3, card_id="T01")

    assert result == "林老師老師 刷卡成功"
    mock_exec.assert_awaited_once_with("register_update_teacher", "T01", 3, fetch=False)
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_card_student_no_teacher_returns_error():
    """Test student swiping on device without active teacher returns failure."""
    student = Cardholder(role="student", card_id="S01", name="王小明")

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=student)),
        patch("app.domains.tutor.process_card.exec_sql", new_callable=AsyncMock, return_value=[]),
    ):
        result = await process_card(device_id=1, card_id="S01")

    assert result == "刷卡失敗: 輔導老師未刷卡"


@pytest.mark.asyncio
async def test_process_card_student_new_appointment():
    """Test student swiping creates new appointment when no existing appointment found."""
    student = Cardholder(role="student", card_id="S01", name="王小明")

    async def side_effect(cmd, *args, **kwargs):
        if cmd == "check_for_teacher":
            return [{"teacher_id": "T01"}]
        if cmd == "register_select":
            return []  # No existing reservation
        return []

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=student)),
        patch("app.domains.tutor.process_card.exec_sql", side_effect=side_effect) as mock_exec,
        patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        result = await process_card(device_id=1, card_id="S01")

    assert result == "王小明學生 刷卡成功"
    # Should call register_insert
    call_args_list = [c.args for c in mock_exec.await_args_list]
    assert ("register_insert", "S01", "T01") in [(c[0], c[1], c[2]) for c in call_args_list if c[0] == "register_insert"]
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_card_student_update_existing_appointment():
    """Test student swiping updates appointment time when existing appointment found."""
    student = Cardholder(role="student", card_id="S01", name="王小明")

    async def side_effect(cmd, *args, **kwargs):
        if cmd == "check_for_teacher":
            return [{"teacher_id": "T01"}]
        if cmd == "register_select":
            return [{"id": 105}]  # Existing reservation ID
        return []

    with (
        patch("app.domains.tutor.process_card.determine_role", AsyncMock(return_value=student)),
        patch("app.domains.tutor.process_card.exec_sql", side_effect=side_effect) as mock_exec,
        patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        result = await process_card(device_id=1, card_id="S01")

    assert result == "王小明學生 刷卡成功"
    # Should call register_update_student with appt_id 105
    call_args_list = [c.args for c in mock_exec.await_args_list]
    assert ("register_update_student", 105) in [(c[0], c[1]) for c in call_args_list if c[0] == "register_update_student"]
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_card_unexpected_error_handling():
    """Test process_card catches unexpected exceptions and returns '刷卡失敗: API 錯誤'."""
    with patch(
        "app.domains.tutor.process_card.determine_role",
        side_effect=Exception("Unexpected DB drop"),
    ):
        result = await process_card(device_id=1, card_id="S01")

    assert result == "刷卡失敗: API 錯誤"
