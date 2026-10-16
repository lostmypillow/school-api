"""Integration test suite executing /courses/syllabus endpoint against a live MSSQL container.

This test requires the MSSQL container running (e.g. `docker compose up -d db`).
It verifies:
1. HTTP GET /courses/syllabus missing query param returns 422.
2. HTTP GET /courses/syllabus with non-matching course_id returns 500 (since 0 rows != 1 row).
3. Data seeded in MSSQL returns 200 OK and strictly satisfies CourseSyllabusModel shape.
4. Error response when MSSQL fails returns 500 with proper error format.
"""
import os
import socket
from typing import AsyncGenerator

import mssql_python
import pytest
import pytest_asyncio
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.core.exec_mssql_async import exec_mssql, exec_mssql_async
from app.domains.courses.router import router as courses_router
from app.domains.courses.schemas import CourseSyllabusModel

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
    with mssql_python.connect(MASTER_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "IF DB_ID('student_db') IS NULL BEGIN CREATE DATABASE student_db; END;"
            )
        conn.commit()

    os.environ["BOOTSTRAP_URL"] = TEST_DB_URL
    os.environ["DB_URL"] = TEST_DB_URL

    exec_mssql("create_tables")


@pytest_asyncio.fixture
async def integration_app_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient targeting FastAPI with courses router and cache bypassed."""
    app = FastAPI()

    async def dummy_cache_dep():
        yield

    for route in courses_router.routes:
        for dep in getattr(route, "dependencies", []):
            app.dependency_overrides[dep.dependency] = dummy_cache_dep

    app.include_router(courses_router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def clean_syllabus_tables():
    """Ensure syllabus and course tables are clean before and after each test."""
    def _truncate():
        with mssql_python.connect(TEST_DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "IF OBJECT_ID('dbo.course_syllabi', 'U') IS NOT NULL DELETE FROM dbo.course_syllabi;"
                )
                cursor.execute("DELETE FROM dbo.courses;")
                cursor.execute("DELETE FROM dbo.department_years;")
                cursor.execute("DELETE FROM dbo.departments;")
                cursor.execute("DELETE FROM dbo.semesters;")
            conn.commit()

    _truncate()
    yield
    _truncate()


@pytest.mark.asyncio
async def test_get_syllabus_integration_missing_param(
    integration_app_client: AsyncClient,
):
    """Test /courses/syllabus returns 422 when course_id query param is omitted."""
    response = await integration_app_client.get("/courses/syllabus")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "course_id"]
        for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_syllabus_integration_no_match_returns_500(
    integration_app_client: AsyncClient,
):
    """Test /courses/syllabus returns 500 when course_id has no match (len != 1)."""
    response = await integration_app_client.get(
        "/courses/syllabus", params={"course_id": "nonexistent_course"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Something went wrong! Error ID:")


@pytest.mark.asyncio
async def test_get_syllabus_integration_values_and_schema(
    integration_app_client: AsyncClient,
):
    """Test /courses/syllabus returns strict CourseSyllabusModel schema when seeded in MSSQL."""
    # Seed parent hierarchy
    await exec_mssql_async(
        "courses/upsert_semester",
        "112_1",
        "112",
        "1",
        "Subj.jsp?year=112&sem=1",
        fetch=False,
    )
    await exec_mssql_async(
        "courses/upsert_department",
        "112_1_300",
        "112_1",
        "112",
        "1",
        "300",
        "Dept CS",
        "Subj.jsp?year=112&sem=1&code=300",
        fetch=False,
    )
    await exec_mssql_async(
        "courses/upsert_department_year",
        "112_1_300_101",
        "112_1_300",
        "112",
        "1",
        "101",
        "CS Year 1",
        "Subj.jsp?year=112&sem=1&code=101",
        fetch=False,
    )
    c1_params = (
        "112_1_101_300001",
        "112_1_300_101",
        "112",
        "1",
        "300001",
        "Algorithms",
        "Subj.jsp?course=300001",
        3,
        "Required",
        "Prof Turing",
        None,
        "1-3",
        None,
        "2-4",
        None,
        None,
        None,
        "Room 404",
        50,
        2,
        "English",
        "Prereq",
        "CS-A",
        "Lab 1",
        "No",
    )
    await exec_mssql_async("courses/upsert_course", *c1_params, fetch=False)

    # Seed syllabus directly in MSSQL
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.course_syllabi (
                    id, course_id, instructor_name, email, instructor_schedule,
                    abstract, syllabus, grading_policy, materials, consultation,
                    ai, notes, sdg, last_updated
                ) VALUES (
                    '112_1_101_300001_syl', '112_1_101_300001', 'Prof Turing', 'turing@ntut.edu.tw', 'Mon 10-12',
                    'Algorithms and complexity', 'Week 1-16 details', 'Exams 100%', 'CLRS book', 'Office 404',
                    'Allowed', 'Strict attendance', 'Goal 4', '2024-03-01 12:00:00'
                )
                """
            )
        conn.commit()

    response = await integration_app_client.get(
        "/courses/syllabus", params={"course_id": "112_1_101_300001"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    model = CourseSyllabusModel.model_validate(data)
    assert model.id == "112_1_101_300001_syl"
    assert model.course_id == "112_1_101_300001"
    assert model.instructor_name == "Prof Turing"
    assert model.email == "turing@ntut.edu.tw"
    assert model.abstract == "Algorithms and complexity"
    assert model.grading_policy == "Exams 100%"
    assert model.ai == "Allowed"


@pytest.mark.asyncio
async def test_get_syllabus_integration_db_error(
    integration_app_client: AsyncClient, monkeypatch
):
    """Test /courses/syllabus returns 500 when DB connection fails."""
    monkeypatch.setenv(
        "DB_URL", "Server=127.0.0.1,9999;Database=nonexistent;UID=bad;PWD=bad;"
    )

    response = await integration_app_client.get(
        "/courses/syllabus", params={"course_id": "112_1_101_300001"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"].startswith("Something went wrong! Error ID:")
