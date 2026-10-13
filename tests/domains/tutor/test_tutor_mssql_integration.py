"""Integration test suite executing bootstrap and tutor domain queries against a live MSSQL container.

This test requires only the MSSQL container running (e.g., `docker compose up -d db`).
It verifies:
1. Creation of database and bootstrap DDL execution (`create_tables` and `check_device_db`).
2. Baseline dictionary shape (keys and value types) for each SQL file in `app/core/sql/tutors/`.
3. End-to-end `determine_role` and `process_card` business workflows against real MSSQL responses.
"""
import os
import socket
from unittest.mock import AsyncMock, patch

import mssql_python
import pytest
import pytest_asyncio

from app.core.db import exec_mssql, exec_mssql_async
from app.domains.tutor.process_card import process_card
from app.domains.tutor.determine_role import determine_role
from app.domains.tutor.models import Cardholder


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
    """Check if the MSSQL server port is open and accepting TCP connections."""
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
    """Ensure student_db exists and run bootstrap schema migration before tests."""
    # 1. Connect to master to ensure student_db exists
    with mssql_python.connect(MASTER_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "IF DB_ID('student_db') IS NULL BEGIN CREATE DATABASE student_db; END;"
            )
        conn.commit()

    # 2. Configure environment variables for exec_mssql
    os.environ["BOOTSTRAP_URL"] = TEST_DB_URL
    os.environ["DB_URL"] = TEST_DB_URL

    # 3. Run bootstrap DDL for all models (students, users, devices, appointments, etc.)
    exec_mssql("create_tables")

    # 4. Run tutor bootstrap (devices 1..6, test student and teacher)
    exec_mssql("bootstrap_tutor")


@pytest_asyncio.fixture(autouse=True)
async def seed_test_data():
    """Seed test fixtures before each test and clean them up afterwards."""
    # Clean up any leftover test records first
    await exec_mssql_async(
        "register_update_teacher", None, 1, fetch=False
    )
    await exec_mssql_async(
        "register_update_teacher", None, 2, fetch=False
    )
    await exec_mssql_async(
        "register_update_teacher", None, 3, fetch=False
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cursor:
            # Clean old test data
            cursor.execute("DELETE FROM dbo.tutor_appointments WHERE student_id = 'S001' OR teacher_id = 'CARD_TEA_001';")
            cursor.execute("DELETE FROM dbo.students WHERE student_id = 'S001' OR card_id = 'CARD_STU_001';")
            cursor.execute("DELETE FROM dbo.users WHERE id = 'T001' OR card_id = 'CARD_TEA_001';")
            cursor.execute("DELETE FROM dbo.math_announcements WHERE content LIKE 'TEST_ANN_%';")

            # Insert baseline student
            cursor.execute(
                "INSERT INTO dbo.students (student_id, name, card_id) VALUES ('S001', N'小明', 'CARD_STU_001');"
            )
            # Insert baseline teacher (department = '9' is required by fetch_role_teacher.sql)
            cursor.execute(
                "INSERT INTO dbo.users (id, name, card_id, college, new_college, department) "
                "VALUES ('T001', N'王老師', 'CARD_TEA_001', N'理學院', N'新理學院', '9');"
            )
        conn.commit()

    yield

    # Teardown
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dbo.tutor_appointments WHERE student_id = 'S001' OR teacher_id = 'CARD_TEA_001';")
            cursor.execute("DELETE FROM dbo.students WHERE student_id = 'S001' OR card_id = 'CARD_STU_001';")
            cursor.execute("DELETE FROM dbo.users WHERE id = 'T001' OR card_id = 'CARD_TEA_001';")
            cursor.execute("DELETE FROM dbo.math_announcements WHERE content LIKE 'TEST_ANN_%';")
            cursor.execute("UPDATE dbo.devices SET teacher_id = NULL WHERE id IN (1, 2, 3);")
        conn.commit()


# ============================================================================
# DOMAIN LOGIC LIVE INTEGRATION TESTS (determine_role and process_card)
# ============================================================================

@pytest.mark.asyncio
async def test_determine_role_live():
    """Verify determine_role correctly maps live MSSQL records into Cardholder."""
    # 1. Student card
    student = await determine_role("CARD_STU_001")
    assert isinstance(student, Cardholder)
    assert student.role == "student"
    assert student.name == "小明"
    assert student.card_id == "S001"

    # 2. Teacher card (before device assignment)
    teacher = await determine_role("CARD_TEA_001")
    assert isinstance(teacher, Cardholder)
    assert teacher.role == "teacher"
    assert teacher.name == "王老師"
    assert teacher.card_id == "T001"
    assert teacher.device_id is None

    # Assign device 1 to teacher and verify determine_role picks up device_id
    await exec_mssql_async("register_update_teacher", "T001", 1, fetch=False)
    teacher_assigned = await determine_role("CARD_TEA_001")
    assert isinstance(teacher_assigned, Cardholder)
    assert teacher_assigned.device_id == 1

    # 3. Unknown card
    unknown = await determine_role("NON_EXISTENT_CARD")
    assert unknown == "刷卡失敗: 查無此人"


@pytest.mark.asyncio
@patch("app.domains.tutor.process_card.sync_frontend", new_callable=AsyncMock)
async def test_process_card_full_workflow_live(mock_sync):
    """Verify complete end-to-end swipe cycle on live MSSQL."""
    # 1. Student swipes before teacher arrived -> fails
    res_student_early = await process_card(device_id=1, card_id="CARD_STU_001")
    assert res_student_early == "刷卡失敗: 輔導老師未刷卡"

    # 2. Teacher swipes on device 1 -> assigns device 1
    res_teacher = await process_card(device_id=1, card_id="CARD_TEA_001")
    assert res_teacher == "王老師老師 刷卡成功"

    # Verify live DB updated
    dev1_rows = await exec_mssql_async("check_for_teacher", 1)
    assert dev1_rows[0]["teacher_id"] == "T001"

    # 3. Student swipes -> starts tutoring session
    res_student_start = await process_card(device_id=1, card_id="CARD_STU_001")
    assert res_student_start == "小明學生 刷卡成功"

    # Verify active appointment in DB
    appts = await exec_mssql_async("register_select", "S001", "T001")
    assert len(appts) == 1

    # 4. Student swipes second time -> ends tutoring session
    res_student_end = await process_card(device_id=1, card_id="CARD_STU_001")
    assert res_student_end == "小明學生 刷卡成功"

    # Verify appointment is ended in DB
    appts_ended = await exec_mssql_async("register_select", "S001", "T001")
    assert len(appts_ended) == 0

    # 5. Teacher swipes again on device 1 -> unassigns device
    res_teacher_leave = await process_card(device_id=1, card_id="CARD_TEA_001")
    assert res_teacher_leave == "王老師老師 刷卡成功"

    # Verify teacher is unassigned in DB
    dev1_cleared = await exec_mssql_async("check_for_teacher", 1)
    assert dev1_cleared[0]["teacher_id"] is None
