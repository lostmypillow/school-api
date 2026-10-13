"""Shared test fixtures for MSSQL core/sql integration tests against a real Docker database."""
import os
import socket

import mssql_python
import pytest
import pytest_asyncio

from app.core.db import exec_mssql


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
    """Ensure student_db exists and run bootstrap schema migration before any SQL tests."""
    if not is_mssql_reachable():
        pytest.skip(f"MSSQL container not reachable at {MSSQL_HOST}:{MSSQL_PORT}")

    os.environ["BOOTSTRAP_URL"] = MASTER_URL
    os.environ["DB_URL"] = TEST_DB_URL

    exec_mssql("create_database")

    exec_mssql("create_tables")

    exec_mssql("bootstrap_tutor")


@pytest_asyncio.fixture(autouse=True)
async def clean_sql_tables():
    """Ensure all test tables are clean before each test runs and clean up after."""
    if not is_mssql_reachable():
        yield
        return

    def _truncate_or_delete():
        with mssql_python.connect(TEST_DB_URL) as conn:
            with conn.cursor() as cursor:
                # Tutor domain tables
                cursor.execute("DELETE FROM dbo.tutor_appointments;")
                cursor.execute("DELETE FROM dbo.students;")
                cursor.execute("DELETE FROM dbo.users;")
                cursor.execute("DELETE FROM dbo.math_announcements;")
                cursor.execute("UPDATE dbo.devices SET teacher_id = NULL;")

                # Course domain tables (in FK order: courses -> department_years -> departments -> semesters)
                cursor.execute("DELETE FROM dbo.courses;")
                cursor.execute("DELETE FROM dbo.department_years;")
                cursor.execute("DELETE FROM dbo.departments;")
                cursor.execute("DELETE FROM dbo.semesters;")
            conn.commit()

    _truncate_or_delete()
    yield
    _truncate_or_delete()
