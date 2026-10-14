"""Integration tests for all course SQL files in app/core/sql/courses/ against real MSSQL."""
from datetime import datetime

import mssql_python
import pytest

from app.core.exec_mssql_async import exec_mssql_async
from tests.sql.conftest import TEST_DB_URL


@pytest.mark.asyncio
async def test_upsert_semester_insert_and_update():
    """Verify courses/upsert_semester.sql baseline: inserts new semester and updates existing on match."""
    # 1. Insert new semester
    res = await exec_mssql_async(
        "courses/upsert_semester",
        "112_1",
        "112",
        "1",
        "https://example.com/sem1",
        fetch=False,
    )
    assert res == []

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, year, sem, link, created_at, updated_at FROM dbo.semesters WHERE id = '112_1';")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "112_1"
            assert row[1] == "112"
            assert row[2] == "1"
            assert row[3] == "https://example.com/sem1"
            created_at_first = row[4]
            assert isinstance(created_at_first, datetime)

    # 2. Update existing semester (change link)
    await exec_mssql_async(
        "courses/upsert_semester",
        "112_1",
        "112",
        "1",
        "https://example.com/sem1_v2",
        fetch=False,
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, year, sem, link, created_at, updated_at FROM dbo.semesters WHERE id = '112_1';")
            row = cur.fetchone()
            assert row[3] == "https://example.com/sem1_v2"
            assert row[4] == created_at_first  # created_at unchanged


@pytest.mark.asyncio
async def test_upsert_semester_batch_params():
    """Verify upsert_semester with batch_params (also testing short name resolution)."""
    batch = [
        ("111_1", "111", "1", "link_111_1"),
        ("111_2", "111", "2", "link_111_2"),
    ]
    # Testing command resolution by short name "upsert_semester"
    res = await exec_mssql_async("upsert_semester", batch_params=batch, fetch=False)
    assert res == []

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dbo.semesters WHERE id IN ('111_1', '111_2');")
            assert cur.fetchone()[0] == 2


@pytest.mark.asyncio
async def test_upsert_department_insert_and_update():
    """Verify courses/upsert_department.sql baseline: inserts and updates departments."""
    # Seed parent semester first
    await exec_mssql_async("courses/upsert_semester", "112_1", "112", "1", "link", fetch=False)

    # 1. Insert department
    await exec_mssql_async(
        "courses/upsert_department",
        "112_1_300",
        "112_1",
        "112",
        "1",
        "300",
        "Computer Science",
        "https://example.com/cs",
        fetch=False,
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, semester_id, year, sem, code, name, link FROM dbo.departments WHERE id = '112_1_300';"
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "112_1_300"
            assert row[1] == "112_1"
            assert row[2] == "112"
            assert row[3] == "1"
            assert row[4] == "300"
            assert row[5] == "Computer Science"
            assert row[6] == "https://example.com/cs"

    # 2. Update department name and link
    await exec_mssql_async(
        "courses/upsert_department",
        "112_1_300",
        "112_1",
        "112",
        "1",
        "300",
        "CS & AI Department",
        "https://example.com/cs_ai",
        fetch=False,
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, link FROM dbo.departments WHERE id = '112_1_300';")
            row = cur.fetchone()
            assert row[0] == "CS & AI Department"
            assert row[1] == "https://example.com/cs_ai"


@pytest.mark.asyncio
async def test_upsert_department_year_insert_and_update():
    """Verify courses/upsert_department_year.sql baseline: inserts and updates department years."""
    # Seed ancestors
    await exec_mssql_async("courses/upsert_semester", "112_1", "112", "1", "link", fetch=False)
    await exec_mssql_async(
        "courses/upsert_department", "112_1_300", "112_1", "112", "1", "300", "CS", "link", fetch=False
    )

    # 1. Insert department_year
    await exec_mssql_async(
        "courses/upsert_department_year",
        "112_1_300_101",
        "112_1_300",
        "112",
        "1",
        "101",
        "CS Year 1",
        "https://example.com/cs_y1",
        fetch=False,
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, department_id, year, sem, code, name, link FROM dbo.department_years WHERE id = '112_1_300_101';"
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "112_1_300_101"
            assert row[1] == "112_1_300"
            assert row[5] == "CS Year 1"

    # 2. Update department_year
    await exec_mssql_async(
        "courses/upsert_department_year",
        "112_1_300_101",
        "112_1_300",
        "112",
        "1",
        "101",
        "CS Freshman Year",
        "https://example.com/cs_y1_v2",
        fetch=False,
    )

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, link FROM dbo.department_years WHERE id = '112_1_300_101';")
            row = cur.fetchone()
            assert row[0] == "CS Freshman Year"
            assert row[1] == "https://example.com/cs_y1_v2"


@pytest.mark.asyncio
async def test_upsert_course_insert_and_update():
    """Verify courses/upsert_course.sql baseline: inserts and updates courses across all 25 fields."""
    # Seed ancestors
    await exec_mssql_async("courses/upsert_semester", "112_1", "112", "1", "link", fetch=False)
    await exec_mssql_async(
        "courses/upsert_department", "112_1_300", "112_1", "112", "1", "300", "CS", "link", fetch=False
    )
    await exec_mssql_async(
        "courses/upsert_department_year", "112_1_300_101", "112_1_300", "112", "1", "101", "CS Y1", "link", fetch=False
    )

    # 1. Insert course (25 parameters)
    course_params = (
        "112_1_101_300001",  # id
        "112_1_300_101",     # department_year_id
        "112",               # year
        "1",                 # sem
        "300001",            # code
        "Algorithms",        # name
        "syllabus.jsp?id=1", # link
        3,                   # credits
        "Required",          # course_type
        "Prof Turing",       # instructor
        None,                # sun
        "1 2 3",             # mon
        None,                # tue
        None,                # wed
        None,                # thu
        None,                # fri
        None,                # sat
        "Room 101",          # classroom
        45,                  # students_enrolled
        1,                   # students_dropped
        "English",           # language
        "Bring laptop",      # notes
        "No",                # with_class
        "Yes",               # experiment
        "No",                # cross_discipline
    )
    await exec_mssql_async("courses/upsert_course", *course_params, fetch=False)

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, credits, instructor, classroom, students_enrolled, language FROM dbo.courses WHERE id = '112_1_101_300001';"
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "112_1_101_300001"
            assert row[1] == "Algorithms"
            assert row[2] == 3
            assert row[3] == "Prof Turing"
            assert row[4] == "Room 101"
            assert row[5] == 45
            assert row[6] == "English"

    # 2. Update course (change instructor, classroom, students_enrolled)
    updated_course_params = list(course_params)
    updated_course_params[9] = "Prof Knuth"    # instructor
    updated_course_params[17] = "Room 202"    # classroom
    updated_course_params[18] = 50            # students_enrolled

    await exec_mssql_async("courses/upsert_course", *updated_course_params, fetch=False)

    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT instructor, classroom, students_enrolled FROM dbo.courses WHERE id = '112_1_101_300001';"
            )
            row = cur.fetchone()
            assert row[0] == "Prof Knuth"
            assert row[1] == "Room 202"
            assert row[2] == 50
