"""Unit tests for Tutor domain routers (announcements, card, update, ws)."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from fastapi import FastAPI, WebSocketDisconnect, status
from httpx import ASGITransport, AsyncClient
import pytest

from app.domains.tutor.router import router as tutor_router
from app.domains.tutor.schemas.announcement import Announcement
from app.domains.tutor.schemas.api_response import APIResponse
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.schemas.update_teacher_response import UpdateTeacherResponse


@pytest.fixture
def test_tutor_app() -> FastAPI:
    app = FastAPI()
    app.include_router(tutor_router)
    return app


@pytest_asyncio.fixture
async def tutor_client(test_tutor_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_tutor_app), base_url="http://test"
    ) as client:
        yield client


# ==============================================================================
# Announcements Endpoints
# ==============================================================================


@pytest.mark.asyncio
async def test_add_announcement_sanitizes_html_and_returns_shape(tutor_client: AsyncClient):
    """Test POST /tutor/announcements/ strips disallowed HTML tags and returns APIResponse."""
    raw_payload = {
        "content": "<h1>Math Quiz</h1><p>Time is 10:00</p><script>alert('xss')</script><iframe src='bad'></iframe>"
    }

    with patch(
            "app.domains.tutor.routers.announcements.exec_sql",
        new_callable=AsyncMock,
    ) as mock_exec:
        response = await tutor_client.post("/tutor/announcements/", json=raw_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = APIResponse.model_validate(data)
    assert validated.detail == "Adding announcement successful!!"

    # Verify script and iframe were stripped by sanitize_html
    sanitized_content = mock_exec.call_args[0][1]
    assert "<script>" not in sanitized_content
    assert "<iframe>" not in sanitized_content
    assert "<h1>Math Quiz</h1>" in sanitized_content
    assert "<p>Time is 10:00</p>" in sanitized_content


@pytest.mark.asyncio
async def test_add_announcement_error_raises_500(tutor_client: AsyncClient):
    """Test POST /tutor/announcements/ returns 500 when database fails."""
    with patch(
            "app.domains.tutor.routers.announcements.exec_sql",
        side_effect=Exception("DB write failure"),
    ):
        response = await tutor_client.post(
            "/tutor/announcements/", json={"content": "Notice"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Error ")


@pytest.mark.asyncio
async def test_update_announcement_success(tutor_client: AsyncClient):
    """Test PUT /tutor/announcements/ returns APIResponse."""
    payload = {"id": 10, "content": "Updated content"}

    with patch(
            "app.domains.tutor.routers.announcements.exec_sql",
        new_callable=AsyncMock,
    ) as mock_exec:
        response = await tutor_client.put("/tutor/announcements/", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = APIResponse.model_validate(data)
    assert validated.detail == "Updating announcement successful!!"
    mock_exec.assert_awaited_once_with(
        "update_announce", 10, "Updated content", fetch=False
    )


@pytest.mark.asyncio
async def test_delete_announcement_success(tutor_client: AsyncClient):
    """Test DELETE /tutor/announcements/{id} returns APIResponse."""
    with patch(
            "app.domains.tutor.routers.announcements.exec_sql",
        new_callable=AsyncMock,
    ) as mock_exec:
        response = await tutor_client.delete("/tutor/announcements/42")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = APIResponse.model_validate(data)
    assert validated.detail == "Deleting announcement successful!!"
    mock_exec.assert_awaited_once_with("delete_announce", 42, fetch=False)


@pytest.mark.asyncio
async def test_get_announcements_returns_list_shape(tutor_client: AsyncClient):
    """Test GET /tutor/announcements/ returns list[Announcement] with exact fields."""
    mock_db_rows = [
        {
            "id": 1,
            "content": "<p>Math tutoring available</p>",
            "created_at": datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            "updated_at": None,
        }
    ]

    with patch(
            "app.domains.tutor.routers.announcements.exec_sql",
        new_callable=AsyncMock,
        return_value=mock_db_rows,
    ):
        response = await tutor_client.get("/tutor/announcements/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    ann = Announcement.model_validate(data[0])
    assert ann.id == 1
    assert ann.content == "<p>Math tutoring available</p>"
    assert ann.created_at is not None
    assert ann.updated_at is None


# ==============================================================================
# Card Swipe & Update Endpoints
# ==============================================================================


@pytest.mark.asyncio
async def test_register_card_id_path_constraints(tutor_client: AsyncClient):
    """Test GET /tutor/card/{device_id}/{card_id} rejects device_id outside 0..6."""
    # device_id = 7 (invalid, must be <= 6)
    resp_high = await tutor_client.get("/tutor/card/7/test_card")
    assert resp_high.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # device_id = -1 (invalid, must be >= 0)
    resp_neg = await tutor_client.get("/tutor/card/-1/test_card")
    assert resp_neg.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_register_card_id_device_zero_teacher(tutor_client: AsyncClient):
    """Test GET /tutor/card/0/{card_id} returns Cardholder JSON for teacher."""
    teacher = Cardholder(role="teacher", card_id="T100", name="林老師", device_id=1)

    with patch(
        "app.domains.tutor.routers.card.process_card",
        new_callable=AsyncMock,
        return_value=teacher,
    ):
        response = await tutor_client.get("/tutor/card/0/T100")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = Cardholder.model_validate(data)
    assert validated.role == "teacher"
    assert validated.card_id == "T100"
    assert validated.name == "林老師"


@pytest.mark.asyncio
async def test_register_card_id_device_swipe_returns_string(tutor_client: AsyncClient):
    """Test GET /tutor/card/1/{card_id} returns swipe message string."""
    with patch(
        "app.domains.tutor.routers.card.process_card",
        new_callable=AsyncMock,
        return_value="王小明學生 刷卡成功",
    ):
        response = await tutor_client.get("/tutor/card/1/S100")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "王小明學生 刷卡成功"


@pytest.mark.asyncio
async def test_card_update_teacher_info(tutor_client: AsyncClient):
    """Test POST /tutor/card/update returns UpdateTeacherResponse."""
    payload = {
        "card_id": "T100",
        "name": "李老師",
        "new_school": "台大",
    }

    with (
        patch("app.domains.tutor.routers.card.exec_sql", new_callable=AsyncMock) as mock_exec,
        patch("app.domains.tutor.routers.card.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        response = await tutor_client.post("/tutor/card/update", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    validated = UpdateTeacherResponse.model_validate(data)
    assert validated.detail == "Update success"

    mock_exec.assert_awaited_once_with(
        "update_teacher_info", "台大", "T100", "T100", fetch=False
    )
    mock_sync.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_teacher_info_endpoint(tutor_client: AsyncClient):
    """Test POST /tutor/update/ returns UpdateTeacherResponse."""
    payload = {
        "card_id": "T200",
        "name": "陳老師",
        "new_school": "清大",
    }

    with (
        patch("app.domains.tutor.routers.update.exec_sql", new_callable=AsyncMock) as mock_exec,
        patch("app.domains.tutor.routers.update.sync_frontend", new_callable=AsyncMock) as mock_sync,
    ):
        response = await tutor_client.post("/tutor/update/", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["detail"] == "Update success"

    mock_exec.assert_awaited_once_with(
        "update_teacher_info", "清大", "T200", "T200", fetch=False
    )
    mock_sync.assert_awaited_once()
