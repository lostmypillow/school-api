"""Tests for built-in database bootstrap commands ('create_database' and 'create_tables') against real MSSQL."""
import mssql_python
import pytest

from app.core.exec_mssql_async import exec_mssql, exec_mssql_async
from tests.sql.conftest import MASTER_URL, TEST_DB_URL


EXPECTED_TABLES = {
    "courses",
    "departments",
    "department_years",
    "devices",
    "math_announcements",
    "semesters",
    "students",
    "tutor_appointments",
    "users",
}


@pytest.mark.asyncio
async def test_create_database_command():
    """Verify 'create_database' command creates student_db if not exists, and is idempotent."""
    # Test sync exec_mssql
    result_sync = exec_mssql("create_database")
    assert result_sync == []

    # Test async exec_mssql_async
    result_async = await exec_mssql_async("create_database")
    assert result_async == []

    # Verify student_db is registered in master.sys.databases
    with mssql_python.connect(MASTER_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM sys.databases WHERE name = N'student_db';")
            rows = cursor.fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "student_db"


@pytest.mark.asyncio
async def test_create_tables_command():
    """Verify 'create_tables' command creates all DDL tables in student_db idempotently."""
    # Execute create_tables
    res = await exec_mssql_async("create_tables", fetch=False)
    assert res == []

    # Query INFORMATION_SCHEMA to verify all tables were created
    with mssql_python.connect(TEST_DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
            )
            rows = cursor.fetchall()
            existing_tables = {row[0] for row in rows}

    missing_tables = EXPECTED_TABLES - existing_tables
    assert not missing_tables, f"Missing tables in student_db: {missing_tables}"

    # Running create_tables again should be completely idempotent
    res_second = await exec_mssql_async("create_tables", fetch=False)
    assert res_second == []
