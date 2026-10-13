import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

# Alias app.database to legacy dependecies for internal domain imports
from app.core.legacy import dependecies
sys.modules["app.database"] = dependecies

from app.domains.internal.trials.router import (  # noqa: E402
    LogRecordCreate,
    LogRecordResponse,
    TrialRecordBase,
    TrialRecordCreate,
    create_trial,
    delete_trial,
    get_managers,
    get_schools,
    read_trial,
    read_trials,
)


# ---------------------------------------------------------------------------
# Pydantic Schema / Model Tests
# ---------------------------------------------------------------------------


def test_trial_record_validation_success():
    """Test TrialRecordBase succeeds when at least one school and one phone are provided."""
    record = TrialRecordBase(
        middle_school_name="仁愛國中",
        telephone="02-12345678",
        student_id="123456",
        student_name="王小明",
    )
    assert record.middle_school_name == "仁愛國中"
    assert record.telephone == "02-12345678"
    assert record.student_id == "123456"


def test_trial_record_validation_missing_schools_error():
    """Test TrialRecordBase raises ValidationError when neither school name is provided."""
    with pytest.raises(ValidationError) as exc_info:
        TrialRecordBase(
            telephone="0912345678",
            student_name="王小明",
        )
    assert "必須提供至少一個學校名稱" in str(exc_info.value)


def test_trial_record_validation_missing_phone_error():
    """Test TrialRecordBase raises ValidationError when neither telephone nor mobile is provided."""
    with pytest.raises(ValidationError) as exc_info:
        TrialRecordBase(
            middle_school_name="仁愛國中",
            student_name="王小明",
        )
    assert "必須提供至少一個聯絡電話" in str(exc_info.value)


def test_trial_record_validation_invalid_student_id():
    """Test TrialRecordBase raises ValidationError when student_id is not exactly 6 digits."""
    with pytest.raises(ValidationError):
        TrialRecordBase(
            middle_school_name="仁愛國中",
            mobile="0912345678",
            student_id="12345",  # 5 digits instead of 6
        )


def test_log_record_schemas():
    """Test LogRecordCreate and LogRecordResponse schemas."""
    log_create = LogRecordCreate(
        employee_name="Alice",
        category="Admin",
        log_content="Logged in",
        computer_name="PC-01",
        employee_id="E1001",
    )
    assert log_create.employee_name == "Alice"

    now = datetime(2026, 1, 1, 12, 0, 0)
    log_resp = LogRecordResponse(
        id=1,
        date=now,
        time=now,
        **log_create.model_dump(),
    )
    assert log_resp.id == 1


# ---------------------------------------------------------------------------
# Router Handler Unit Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_managers_handler():
    """Test get_managers returns list of manager names from DB."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = ["Manager 1", "Manager 2"]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    managers = await get_managers(db=mock_session)
    assert managers == ["Manager 1", "Manager 2"]


@pytest.mark.asyncio
async def test_get_schools_handler():
    """Test get_schools returns list of SchoolRecord items."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_row1 = {"id": 1, "name": "School A", "city": "Taipei"}
    mock_row2 = {"id": 2, "name": "School B", "city": "New Taipei"}

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [mock_row1, mock_row2]
    mock_session.execute = AsyncMock(return_value=mock_result)

    schools = await get_schools(db=mock_session, level="middle")
    assert len(schools) == 2
    assert schools[0]["name"] == "School A"


@pytest.mark.asyncio
async def test_create_trial_handler():
    """Test create_trial inserts record and returns created object."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_row = {
        "id": 10,
        "created_at": datetime(2026, 1, 1, 0, 0, 0),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0),
    }
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    payload = TrialRecordCreate(
        source="Web",
        student_id="123456",
        student_name="Test Student",
        middle_school_name="MS",
        telephone="02-88888888",
    )

    created = await create_trial(payload, db=mock_session)
    assert created["id"] == 10
    assert created["student_name"] == "Test Student"


@pytest.mark.asyncio
async def test_read_trials_handler():
    """Test read_trials returns paged data and total count."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_rows = [
        {"id": 1, "student_name": "S1", "total_count": 1},
    ]
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = mock_rows
    mock_session.execute = AsyncMock(return_value=mock_result)

    res = await read_trials(db=mock_session, skip=0, limit=10)
    assert res["total"] == 1
    assert len(res["data"]) == 1


@pytest.mark.asyncio
async def test_read_trial_not_found():
    """Test read_trial raises 404 when trial ID is not found."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await read_trial(trial_id=999, db=mock_session)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_trial_not_found():
    """Test delete_trial raises 404 when trial ID does not exist."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await delete_trial(trial_id=999, db=mock_session)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
