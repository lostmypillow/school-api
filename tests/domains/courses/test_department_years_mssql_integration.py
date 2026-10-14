"""Integration test suite executing /courses/department_years endpoint against a live MSSQL container.

This test requires the MSSQL container running (e.g. `docker compose up -d db`).
It verifies:
1. HTTP GET /courses/department_years missing query param returns 422.
2. HTTP GET /courses/department_years with non-matching department_id returns 200 OK and [].
3. Data seeded in MSSQL via upsert_department_year returns 200 OK, filters by department_id,
   and strictly satisfies DepartmentYearResponseSchema.
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
async def test_get_department_years_integration_missing_param(
    integration_app_client: AsyncClient,
):
    """Test /courses/department_years returns 422 when department_id query param is omitted."""
    response = await integration_app_client.get("/courses/department_years")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()
    assert "detail" in errors
    assert any(
        err.get("loc") == ["query", "department_id"] for err in errors["detail"]
    )


@pytest.mark.asyncio
async def test_get_department_years_integration_empty_when_no_match(
    integration_app_client: AsyncClient,
):
    """Test /courses/department_years returns 200 OK and [] when department_id has no matches."""
    response = await integration_app_client.get(
        "/courses/department_years", params={"department_id": "nonexistent"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_department_years_integration_values_and_schema(
    integration_app_client: AsyncClient,
):
    """Test /courses/department_years returns accurate records and strictly validates against DepartmentYearResponseSchema."""
    # Seed parent ancestors
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

    # Seed department years under 112_1_300
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
    await exec_mssql_async(
        "courses/upsert_department_year",
        "112_1_300_102",
        "112_1_300",
        "112",
        "1",
        "102",
        "CS Year 2",
        "Subj.jsp?year=112&sem=1&code=102",
        fetch=False,
    )

    # Seed department year under 112_1_400 (should be excluded by filter)
    await exec_mssql_async(
        "courses/upsert_department_year",
        "112_1_400_201",
        "112_1_400",
        "112",
        "1",
        "201",
        "EE Year 1",
        "Subj.jsp?year=112&sem=1&code=201",
        fetch=False,
    )

    response = await integration_app_client.get(
        "/courses/department_years", params={"department_id": "112_1_300"}
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2

    for item in data:
        assert item["department_id"] == "112_1_300"

    dy_by_id = {item["id"]: item for item in data}
    assert "112_1_300_101" in dy_by_id
    assert "112_1_300_102" in dy_by_id
    assert "112_1_400_201" not in dy_by_id

    dy1 = dy_by_id["112_1_300_101"]
    assert dy1["name"] == "CS Year 1"
    assert dy1["code"] == "101"
    assert dy1["year"] == "112"
    assert dy1["sem"] == "1"
    assert dy1["link"] == "Subj.jsp?year=112&sem=1&code=101"
    assert isinstance(dy1["created_at"], str)
    assert isinstance(dy1["updated_at"], str)

    dy2 = dy_by_id["112_1_300_102"]
    assert dy2["name"] == "CS Year 2"
    assert dy2["code"] == "102"


@pytest.mark.asyncio
async def test_get_department_years_integration_db_error(
    integration_app_client: AsyncClient, monkeypatch
):
    """Test /courses/department_years handles DB connection failures by returning 500 via HTTP."""
    monkeypatch.setenv(
        "DB_URL", "Server=127.0.0.1,9999;Database=nonexistent;UID=bad;PWD=bad;"
    )

    response = await integration_app_client.get(
        "/courses/department_years", params={"department_id": "112_1_300"}
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    body = response.json()
    assert "detail" in body
    assert body["detail"].startswith("Something went wrong! Error ID:")
