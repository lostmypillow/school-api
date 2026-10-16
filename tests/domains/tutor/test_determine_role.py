"""Unit tests for determine_role in Tutor domain."""
from unittest.mock import AsyncMock, patch
import pytest

from app.domains.tutor.determine_role import determine_role
from app.domains.tutor.schemas.cardholder import Cardholder


@pytest.mark.asyncio
async def test_determine_role_student():
    """Test determine_role returns Cardholder with role='student' when student record exists."""
    student_db_row = [
        {
            "student_id": " 111111 ",
            "name": "王小明",
            "college": "資訊學院",
        }
    ]

    with patch(
        "app.domains.tutor.determine_role.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=student_db_row,
    ) as mock_exec:
        result = await determine_role("111111")

    assert isinstance(result, Cardholder)
    assert result.role == "student"
    assert result.card_id == "111111"  # Stripped
    assert result.name == "王小明"
    assert result.school == "資訊學院"
    assert result.device_id is None

    mock_exec.assert_awaited_once_with("fetch_role_student", "111111", "111111")


@pytest.mark.asyncio
async def test_determine_role_teacher_with_assigned_device():
    """Test determine_role returns Cardholder with role='teacher' and device_id."""
    teacher_db_row = [
        {
            "id": " 222222 ",
            "name": "李老師",
            "college": "電資學院",
        }
    ]
    device_db_row = [{"id": 3}]

    async def side_effect(command_name, *args, **kwargs):
        if command_name == "fetch_role_student":
            return []
        if command_name == "fetch_role_teacher":
            return teacher_db_row
        if command_name == "fetch_associated_device":
            return device_db_row
        return []

    with patch(
        "app.domains.tutor.determine_role.exec_mssql_async",
        side_effect=side_effect,
    ):
        result = await determine_role("222222")

    assert isinstance(result, Cardholder)
    assert result.role == "teacher"
    assert result.card_id == "222222"
    assert result.name == "李老師"
    assert result.school == "電資學院"
    assert result.device_id == 3


@pytest.mark.asyncio
async def test_determine_role_teacher_without_device():
    """Test determine_role returns Cardholder with device_id=None when no device assigned."""
    teacher_db_row = [{"id": "222222", "name": "李老師", "college": "電資學院"}]

    async def side_effect(command_name, *args, **kwargs):
        if command_name == "fetch_role_student":
            return []
        if command_name == "fetch_role_teacher":
            return teacher_db_row
        if command_name == "fetch_associated_device":
            return []
        return []

    with patch(
        "app.domains.tutor.determine_role.exec_mssql_async",
        side_effect=side_effect,
    ):
        result = await determine_role("222222")

    assert isinstance(result, Cardholder)
    assert result.role == "teacher"
    assert result.device_id is None


@pytest.mark.asyncio
async def test_determine_role_not_found():
    """Test determine_role returns exact error string '刷卡失敗: 查無此人' when not in DB."""
    with patch(
        "app.domains.tutor.determine_role.exec_mssql_async",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await determine_role("999999")

    assert isinstance(result, str)
    assert result == "刷卡失敗: 查無此人"
