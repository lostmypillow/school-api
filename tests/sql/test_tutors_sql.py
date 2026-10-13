"""Integration tests for all tutor SQL files in app/core/sql/tutors/ against real MSSQL."""
from datetime import datetime

import mssql_python
import pytest

from app.core.db import exec_mssql_async
from tests.sql.conftest import TEST_DB_URL




@pytest.mark.asyncio
async def test_announcements_crud_lifecycle_and_baseline_shape():
    """Test insert_announce, get_announce, update_announce, and delete_announce."""
    await exec_mssql_async("insert_announce", "Test Announcement!", fetch=False)

    rows = await exec_mssql_async(command_name="get_announce")
    assert isinstance(rows, list)
    assert len(rows) >= 1

    ann = next((r for r in rows if r.get("content") == "Test Announcement!"), None)
    assert ann is not None
    assert set(ann.keys()) == {"id", "content", "created_at", "updated_at"}
    assert isinstance(ann["id"], int)
    assert isinstance(ann["content"], str)
    assert isinstance(ann["created_at"], datetime)
    assert ann["updated_at"] is None

    ann_id = ann["id"]

    await exec_mssql_async("update_announce", "Test Announcement! (Updated)", ann_id, fetch=False)

    rows_updated = await exec_mssql_async(command_name="get_announce")
    updated_ann = next(r for r in rows_updated if r["id"] == ann_id)
    assert updated_ann["content"] == "Test Announcement! (Updated)"
    assert isinstance(updated_ann["updated_at"], datetime)

    await exec_mssql_async("delete_announce", ann_id, fetch=False)

    rows_after_delete = await exec_mssql_async(command_name="get_announce")
    assert not any(r["id"] == ann_id for r in rows_after_delete)


@pytest.mark.asyncio
async def test_bootstrap_tutor_and_select_device_db():
    """Test bootstrap_tutor seeds devices 1..6, student 111111, and teacher 222222."""
    await exec_mssql_async("tutors/bootstrap_tutor", fetch=False)

    # 1. select_device_db baseline shape: {'id', 'teacher_id'}
    devices = await exec_mssql_async("select_device_db")
    assert isinstance(devices, list)
    assert len(devices) >= 6

    device_ids = {dev["id"] for dev in devices}
    assert {1, 2, 3, 4, 5, 6}.issubset(device_ids)

    # 2. Verify test student 111111 bootstrapped
    students = await exec_mssql_async("fetch_role_student", "111111", "111111")
    assert len(students) == 1
    assert students[0]["student_id"] == "111111"

    # 3. Verify test teacher 222222 bootstrapped
    teachers = await exec_mssql_async("fetch_role_teacher", "222222", "222222")
    assert len(teachers) == 1
    assert teachers[0]["id"] == "222222"

    # 4. Idempotency: running bootstrap_tutor again should succeed without error
    await exec_mssql_async("tutors/bootstrap_tutor", fetch=False)


@pytest.mark.asyncio
async def test_device_teacher_assignment_and_queries():
    """Verify check_for_teacher, register_update_teacher, and fetch_associated_device."""
    # Ensure devices initialized
    await exec_mssql_async("tutors/bootstrap_tutor", fetch=False)

    # 1. check_for_teacher when unassigned
    dev1 = await exec_mssql_async("check_for_teacher", 1)
    assert isinstance(dev1, list)
    assert len(dev1) == 1
    assert set(dev1[0].keys()) == {"teacher_id"}
    assert dev1[0]["teacher_id"] is None

    # 2. fetch_associated_device when teacher not assigned
    unassigned = await exec_mssql_async("fetch_associated_device", "T_TEST_01")
    assert unassigned == []

    # 3. register_update_teacher: assign teacher to device 1
    await exec_mssql_async("register_update_teacher", "T_TEST_01", 1, fetch=False)

    # check_for_teacher after assignment
    dev1_assigned = await exec_mssql_async("check_for_teacher", 1)
    assert dev1_assigned[0]["teacher_id"] == "T_TEST_01"

    # fetch_associated_device baseline shape: {'id'}
    associated = await exec_mssql_async("fetch_associated_device", "T_TEST_01")
    assert isinstance(associated, list)
    assert len(associated) == 1
    assert set(associated[0].keys()) == {"id"}
    assert associated[0]["id"] == 1
    assert isinstance(associated[0]["id"], int)

    # 4. register_update_teacher: unassign teacher from device 1
    await exec_mssql_async("register_update_teacher", None, 1, fetch=False)

    dev1_cleared = await exec_mssql_async("check_for_teacher", 1)
    assert dev1_cleared[0]["teacher_id"] is None

    associated_cleared = await exec_mssql_async("fetch_associated_device", "T_TEST_01")
    assert associated_cleared == []



@pytest.mark.asyncio
async def test_insert_mock_user_fetch_role_teacher_and_update_teacher_info():
    """Verify insert_mock_user, fetch_role_teacher, and update_teacher_info."""
    # 1. insert_mock_user
    await exec_mssql_async(
        "insert_mock_user",
        "T001",
        "王老師",
        "CARD_TEA_001",
        "理學院",
        "新理學院",
        "9",
        fetch=False,
    )

    # 2. fetch_role_teacher matching by card_id
    rows_by_card = await exec_mssql_async("fetch_role_teacher", "CARD_TEA_001", "CARD_TEA_001")
    assert isinstance(rows_by_card, list)
    assert len(rows_by_card) == 1

    teacher = rows_by_card[0]
    assert set(teacher.keys()) == {"name", "id", "college", "new_college"}
    assert teacher["name"] == "王老師"
    assert teacher["id"] == "T001"
    assert teacher["college"] == "理學院"
    assert teacher["new_college"] == "新理學院"

    # fetch_role_teacher matching by id
    rows_by_id = await exec_mssql_async("fetch_role_teacher", "T001", "T001")
    assert len(rows_by_id) == 1
    assert rows_by_id[0]["id"] == "T001"

    # fetch_role_teacher with nonexistent card/id returns []
    rows_nonexistent = await exec_mssql_async("fetch_role_teacher", "NONEXISTENT", "NONEXISTENT")
    assert rows_nonexistent == []

    # 3. update_teacher_info: updates new_college
    await exec_mssql_async(
        "update_teacher_info",
        "最新理學院",
        "CARD_TEA_001",
        "T001",
        fetch=False,
    )

    rows_updated = await exec_mssql_async("fetch_role_teacher", "CARD_TEA_001", "CARD_TEA_001")
    assert rows_updated[0]["new_college"] == "最新理學院"


@pytest.mark.asyncio
async def test_fetch_role_student_shape_and_filtering():
    """Verify tutors/fetch_role_student.sql baseline shape: {'name', 'student_id'}."""
    # Seed student record
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dbo.students (student_id, name, card_id) "
                "VALUES ('S101', N'小明', 'CARD_STU_101');"
            )
        conn.commit()

    # Query by card_id
    rows_by_card = await exec_mssql_async("fetch_role_student", "CARD_STU_101", "CARD_STU_101")
    assert isinstance(rows_by_card, list)
    assert len(rows_by_card) == 1

    student = rows_by_card[0]
    assert set(student.keys()) == {"name", "student_id"}
    assert student["name"] == "小明"
    assert student["student_id"] == "S101"
    assert isinstance(student["name"], str)
    assert isinstance(student["student_id"], str)

    # Query by student_id
    rows_by_id = await exec_mssql_async("fetch_role_student", "S101", "S101")
    assert len(rows_by_id) == 1
    assert rows_by_id[0]["student_id"] == "S101"

    # Nonexistent card/id returns []
    rows_none = await exec_mssql_async("fetch_role_student", "NO_SUCH_CARD", "NO_SUCH_CARD")
    assert rows_none == []


# ============================================================================
# 5. TUTOR APPOINTMENTS SQL COMMANDS
# ============================================================================

@pytest.mark.asyncio
async def test_register_appointment_lifecycle_and_baseline_shape():
    """Verify register_insert, register_select, and register_update_student."""
    student_id = "S101"
    teacher_id = "T001"

    # 1. Before insert: register_select should return []
    initial = await exec_mssql_async("register_select", student_id, teacher_id)
    assert initial == []

    # 2. register_insert: creates active appointment
    await exec_mssql_async("register_insert", student_id, teacher_id, fetch=False)

    # 3. register_select baseline shape: {'id'}
    active_rows = await exec_mssql_async("register_select", student_id, teacher_id)
    assert isinstance(active_rows, list)
    assert len(active_rows) == 1
    assert set(active_rows[0].keys()) == {"id"}
    appt_id = active_rows[0]["id"]
    assert isinstance(appt_id, int)

    # Verify start_time is set and end_time is NULL in DB
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student_id, teacher_id, start_time, end_time FROM dbo.tutor_appointments WHERE id = ?;",
                appt_id,
            )
            appt_row = cur.fetchone()
            assert appt_row[0] == student_id
            assert appt_row[1] == teacher_id
            assert isinstance(appt_row[2], datetime)
            assert appt_row[3] is None

    # 4. register_update_student: ends active appointment
    await exec_mssql_async("register_update_student", appt_id, fetch=False)

    # Subsequent register_select should return [] since end_time IS NOT NULL
    ended_rows = await exec_mssql_async("register_select", student_id, teacher_id)
    assert ended_rows == []

    # Verify end_time is populated
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT end_time FROM dbo.tutor_appointments WHERE id = ?;", appt_id)
            end_time = cur.fetchone()[0]
            assert isinstance(end_time, datetime)
