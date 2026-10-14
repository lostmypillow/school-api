"""Integration test suite executing /courses/departments endpoint against a live MSSQL container.

This test requires the MSSQL container running (e.g. `docker compose up -d db`).
It verifies:
1. HTTP GET /courses/departments missing query param returns 422.
2. HTTP GET /courses/departments with non-matching semester_id returns 200 OK and [].
3. Data seeded in MSSQL via upsert_department returns 200 OK, filters by semester_id,
   and strictly satisfies DepartmentResponseSchema.
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
async def clean_course_tables():
    """Ensure course tables are clean before and after each test."""
    def _truncate():
        with mssql_python.connect(TEST_DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM dbo.courses;")
                cursor.execute("DELETE FROM dbo.department_years;")
                cursor.execute("DELETE FROM dbo.departments;")
                cursor.execute("DELETE FROM dbo.semesters;")
            conn.commit()

    _truncate()
    yield
    _truncate()


@pytest.mark.asyncio
async def test_get_departments_integration_missing_param(
    integration_app_client: AsyncClient,
):
    """Test /courses/departments returns 422 when semester_id query param is omitted."""
    response = await integration_app_client.get("/courses/departments")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "semester_id"] for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_departments_integration_empty_when_no_match(
    integration_app_client: AsyncClient,
):
    """Test /courses/departments returns 200 OK and [] when semester_id has no matches."""
    response = await integration_app_client.get(
        "/courses/departments", params={"semester_id": "nonexistent"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_departments_integration_values_and_schema(
    integration_app_client: AsyncClient,
):
    """Test /courses/departments returns accurate records and strictly validates against DepartmentResponseSchema."""
    # Seed parent semesters
    await exec_mssql_async(
        "courses/upsert_semester",
        "112_1",
        "112",
        "1",
        "Subj.jsp?year=112&sem=1",
        fetch=False,
    )
    await exec_mssql_async(
        "courses/upsert_semester",
        "112_2",
        "112",
        "2",
        "Subj.jsp?year=112&sem=2",
        fetch=False,
    )

    # Seed departments under 112_1
    await exec_mssql_async(
        "courses/upsert_department",
        "112_1_300",
        "112_1",
        "112",
        "1",
        "300",
        "Computer Science",
        "Subj.jsp?year=112&sem=1&code=300",
        fetch=False,
    )
    await exec_mssql_async(
        "courses/upsert_department",
        "112_1_400",
        "112_1",
        "112",
        "1",
        "400",
        "Electrical Engineering",
        "Subj.jsp?year=112&sem=1&code=400",
        fetch=False,
    )

    # Seed department under 112_2 (should be excluded by filter)
    await exec_mssql_async(
        "courses/upsert_department",
        "112_2_300",
        "112_2",
        "112",
        "2",
        "300",
        "Computer Science Sem2",
        "Subj.jsp?year=112&sem=2&code=300",
        fetch=False,
    )

    response = await integration_app_client.get(
        "/courses/departments", params={"semester_id": "112_1"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    for item in data:
        assert item["semester_id"] == "112_1"

    dept_by_id = {item["id"]: item for item in data}
    assert "112_1_300" in dept_by_id
    assert "112_1_400" in dept_by_id
    assert "112_2_300" not in dept_by_id

    d1 = dept_by_id["112_1_300"]
    assert d1["name"] == "Computer Science"
    assert d1["code"] == "300"
    assert d1["year"] == "112"
    assert d1["sem"] == "1"
    assert d1["link"] == "Subj.jsp?year=112&sem=1&code=300"
    assert isinstance(d1["created_at"], str)
    assert isinstance(d1["updated_at"], str)

    d2 = dept_by_id["112_1_400"]
    assert d2["name"] == "Electrical Engineering"
    assert d2["code"] == "400"


@pytest.mark.asyncio
async def test_get_departments_integration_db_error(
    integration_app_client: AsyncClient, monkeypatch
):
    """Test /courses/departments handles DB connection failures by returning 500 via HTTP."""
    monkeypatch.setenv(
        "DB_URL", "Server=127.0.0.1,9999;Database=nonexistent;UID=bad;PWD=bad;"
    )

    response = await integration_app_client.get(
        "/courses/departments", params={"semester_id": "112_1"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
