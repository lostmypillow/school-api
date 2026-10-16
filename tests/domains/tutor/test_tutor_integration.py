"""Integration test suite executing Tutor domain endpoints against a live MSSQL container.

This test requires the MSSQL container running (e.g. `docker compose up -d db`).
It verifies:
1. Device 0 teacher query returns Cardholder model.
2. Device 0 non-existent cardholder returns 404.
3. Card swipes on devices 1..6 for teacher device assignment and student check-ins.
4. Student swiping on an empty device returns "刷卡失敗: 輔導老師未刷卡".
5. Announcements CRUD lifecycle via HTTP.
6. Teacher update endpoints (/tutor/card/update and /tutor/update/).
"""
import os
import socket
from typing import AsyncGenerator

import mssql_python
import pytest
import pytest_asyncio
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.core.exec_mssql_async import exec_mssql
from app.domains.tutor.router import router as tutor_router
from app.domains.tutor.schemas.announcement import Announcement
from app.domains.tutor.schemas.api_response import APIResponse
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.schemas.update_teacher_response import UpdateTeacherResponse

MSSQL_HOST = os.getenv("TEST_MSSQL_HOST", "127.0.0.1")
MSSQL_PORT = int(os.getenv("TEST_MSSQL_PORT", "1433"))
MSSQL_USER = os.getenv("TEST_MSSQL_USER", "sa")
MSSQL_PASSWORD = os.getenv("TEST_MSSQL_PASSWORD", "YourPassword123!")

MASTER_URL = (
    f"Server={MSSQL_HOST},{MSSQL_PORT};Database=master;"
    f"UID={MSSQL_USER};PWD={MSSQL_PASSWORD};Encrypt=no;TrustServerCertificate=yes;"
)
TEST_DB_URL = (
    f"Server={MSSQL_HOST},{MSSQL_PORT};Database=student_db;"
    f"UID={MSSQL_USER};PWD={MSSQL_PASSWORD};Encrypt=no;TrustServerCertificate=yes;"
)


def is_mssql_reachable() -> bool:
    """Check if MSSQL container is accessible."""
    try:
        with socket.create_connection((MSSQL_HOST, MSSQL_PORT), timeout=1.5):
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not is_mssql_reachable(),
        reason=f"MSSQL container not reachable at {MSSQL_HOST}:{MSSQL_PORT}. "
        "Start it with: docker compose up -d db",
    ),
]


@pytest.fixture(scope="session", autouse=True)
def setup_mssql_database():
    """Ensure student_db exists and run bootstrap tables and tutor seeds before tests."""
    with mssql_python.connect(MASTER_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "IF DB_ID('student_db') IS NULL BEGIN CREATE DATABASE student_db; END;"
            )
        conn.commit()

    os.environ["BOOTSTRAP_URL"] = TEST_DB_URL
    os.environ["DB_URL"] = TEST_DB_URL

    exec_mssql("create_tables")
    exec_mssql("tutors/bootstrap_tutor")


@pytest_asyncio.fixture
async def tutor_app_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient targeting FastAPI with tutor router."""
    app = FastAPI()
    app.include_router(tutor_router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def reset_tutor_state():
    """Reset tutor tables to a known clean state before and after each test."""
    def _reset():
        with mssql_python.connect(TEST_DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM dbo.tutor_appointments;")
                cursor.execute("DELETE FROM dbo.math_announcements;")
                cursor.execute("UPDATE dbo.devices SET teacher_id = NULL;")
                # Ensure seed teacher and student exist
                cursor.execute("IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE id = '222222') "
                               "INSERT INTO dbo.users (id, name, college) VALUES ('222222', '李老師', '電資學院');")
                cursor.execute("IF NOT EXISTS (SELECT 1 FROM dbo.students WHERE student_id = '111111') "
                               "INSERT INTO dbo.students (student_id, name, college) VALUES ('111111', '王小明', '資訊學院');")
            conn.commit()

    _reset()
    yield
    _reset()


@pytest.mark.asyncio
async def test_tutor_card_lookup_device_zero(tutor_app_client: AsyncClient):
    """Test device 0 returns Cardholder for teacher, and 404 when not found."""
    # Teacher 222222 lookup
    resp = await tutor_app_client.get("/tutor/card/0/222222")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    model = Cardholder.model_validate(data)
    assert model.card_id == "222222"
    assert model.role == "teacher"
    assert model.name == "李老師"

    # Unknown user on device 0 -> 404
    resp_404 = await tutor_app_client.get("/tutor/card/0/999999")
    assert resp_404.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_tutor_card_swipe_lifecycle(tutor_app_client: AsyncClient):
    """Test teacher device assignment, student check-in, check-out, and unassignment."""
    # 1. Student swipes on device 1 before teacher -> failure
    resp_no_teacher = await tutor_app_client.get("/tutor/card/1/111111")
    assert resp_no_teacher.status_code == status.HTTP_200_OK
    assert resp_no_teacher.json() == "刷卡失敗: 輔導老師未刷卡"

    # 2. Teacher 222222 swipes on device 1 -> assigned
    resp_teacher_swipe = await tutor_app_client.get("/tutor/card/1/222222")
    assert resp_teacher_swipe.status_code == status.HTTP_200_OK
    assert "刷卡成功" in resp_teacher_swipe.json()

    # 3. Student 111111 swipes on device 1 -> initial appointment created
    resp_student_swipe1 = await tutor_app_client.get("/tutor/card/1/111111")
    assert resp_student_swipe1.status_code == status.HTTP_200_OK
    assert "學生 刷卡成功" in resp_student_swipe1.json()

    # 4. Student 111111 swipes again -> existing appointment updated
    resp_student_swipe2 = await tutor_app_client.get("/tutor/card/1/111111")
    assert resp_student_swipe2.status_code == status.HTTP_200_OK
    assert "學生 刷卡成功" in resp_student_swipe2.json()

    # 5. Teacher swipes on same device 1 -> unassigned
    resp_teacher_unassign = await tutor_app_client.get("/tutor/card/1/222222")
    assert resp_teacher_unassign.status_code == status.HTTP_200_OK
    assert "刷卡成功" in resp_teacher_unassign.json()

    # 6. Now student swipes again -> teacher is no longer on device 1
    resp_student_after_unassign = await tutor_app_client.get("/tutor/card/1/111111")
    assert resp_student_after_unassign.status_code == status.HTTP_200_OK
    assert resp_student_after_unassign.json() == "刷卡失敗: 輔導老師未刷卡"


@pytest.mark.asyncio
async def test_tutor_announcements_integration_lifecycle(tutor_app_client: AsyncClient):
    """Test announcement creation, retrieval, and deletion through HTTP endpoints."""
    # 1. Post announcement
    post_resp = await tutor_app_client.post(
        "/tutor/announcements/",
        json={"content": "<h3>微積分輔導時段</h3><p>週三下午 14:00-16:00</p>"},
    )
    assert post_resp.status_code == status.HTTP_200_OK
    post_data = APIResponse.model_validate(post_resp.json())
    assert post_data.detail == "Adding announcement successful!!"

    # 2. Get announcements
    get_resp = await tutor_app_client.get("/tutor/announcements/")
    assert get_resp.status_code == status.HTTP_200_OK
    items = [Announcement.model_validate(item) for item in get_resp.json()]
    assert len(items) >= 1
    created_item = next(i for i in items if "微積分輔導時段" in i.content)
    assert created_item.id is not None

    # 3. Delete announcement
    del_resp = await tutor_app_client.delete(f"/tutor/announcements/{created_item.id}")
    assert del_resp.status_code == status.HTTP_200_OK
    del_data = APIResponse.model_validate(del_resp.json())
    assert del_data.detail == "Deleting announcement successful!!"


@pytest.mark.asyncio
async def test_tutor_update_teacher_integration(tutor_app_client: AsyncClient):
    """Test updating teacher information via /tutor/update/ and /tutor/card/update."""
    payload = {
        "card_id": "222222",
        "name": "李老師",
        "new_school": "台科大",
    }

    # /tutor/update/
    resp1 = await tutor_app_client.post("/tutor/update/", json=payload)
    assert resp1.status_code == status.HTTP_200_OK
    data1 = UpdateTeacherResponse.model_validate(resp1.json())
    assert data1.detail == "Update success"

    # /tutor/card/update
    resp2 = await tutor_app_client.post("/tutor/card/update", json=payload)
    assert resp2.status_code == status.HTTP_200_OK
    data2 = UpdateTeacherResponse.model_validate(resp2.json())
    assert data2.detail == "Update success"
